from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_sam as sam
from aws_cdk import aws_iam as iam

bundle_python_function_with_requirements = cdk.BundlingOptions(
    image=lambda_.Runtime.PYTHON_3_9.bundling_docker_image,
    command=[
        "/bin/bash",
        "-c",
        (
            "python -m venv .venv &&"
            ".venv/bin/python -m pip install -r /asset-input/requirements.txt &&"
            "cp -r .venv/lib/python3.9/site-packages/* /asset-output/"
            "; cp /asset-input/*.py /asset-output/"
        ),
    ],
    user="root",
)


class CdkStack(cdk.Stack):
    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # issuers_table = dynamodb.Table(
        #     self,
        #     "IssuersTable",
        #     billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        # )

        issuers_table_key_schema = dynamodb.CfnTable.KeySchemaProperty(
            attribute_name="issuer_currency", key_type="HASH"
        )
        issuers_table = dynamodb.CfnTable(
            self,
            "IssuersTable",
            table_name="IssuersTable",
            key_schema=[issuers_table_key_schema],
            attribute_definitions=[
                dynamodb.CfnTable.AttributeDefinitionProperty(
                    attribute_name="issuer_currency", attribute_type="S"
                ),
            ],
            billing_mode="PAY_PER_REQUEST",
        )
        # issuers_table = sam.CfnSimpleTable(
        #     self,
        #     "IssuersTable",
        #     table_name="IssuersTable",
        #     key_schema=[issuers_table_key_schema],
        #     attribute_definitions=[
        #         dynamodb.CfnTable.AttributeDefinitionProperty(
        #             attribute_name="issuer_currency", attribute_type="S"
        #         ),
        #     ],
        #     billing_mode="PAY_PER_REQUEST",
        # )

        generate_issuers_function = lambda_.Function(
            self,
            "GenerateIssuersFunction",
            code=lambda_.Code.from_asset(
                "functions/generate_issuers/",
                bundling=bundle_python_function_with_requirements,
            ),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="function.handler",
            timeout=cdk.Duration.seconds(60),
            environment={
                "ISSUERS_TABLE_NAME": issuers_table.table_name,
            },
        )
        # add table r/w permissions to our issuer generator
        issuers_table_dynamodb_crud_statement = iam.PolicyStatement(
            actions=[
                "dynamodb:BatchGetItem",
                "dynamodb:GetItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "dynamodb:BatchWriteItem",
                "dynamodb:PutItem",
                "dynamodb:UpdateItem",
            ],
            effect=iam.Effect.ALLOW,
            resources=[
                f"arn:aws:dynamodb:*:*:table/{issuers_table.table_name}",
            ],
        )
        generate_issuers_function.add_to_role_policy(
            issuers_table_dynamodb_crud_statement
        )

        generate_faucet_wallet_function = lambda_.Function(
            self,
            "GenerateFaucetWalletFunction",
            code=lambda_.Code.from_asset(
                "functions/faucet_wallet/",
                bundling=bundle_python_function_with_requirements,
            ),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="function.handler",
            timeout=cdk.Duration.seconds(65),
            memory_size=256,
        )

        grab_order_book_function = lambda_.Function(
            self,
            "GrabOrderBookFunction",
            code=lambda_.Code.from_asset(
                "functions/grab_order_book/",
                bundling=bundle_python_function_with_requirements,
            ),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="function.handler",
            timeout=cdk.Duration.seconds(18),
        )

        generate_orders_function = lambda_.Function(
            self,
            "GenerateOrdersFunction",
            code=lambda_.Code.from_asset(
                "functions/generate_orders_function/",
                bundling=bundle_python_function_with_requirements,
            ),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="function.handler",
            timeout=cdk.Duration.seconds(900),
            memory_size=512,
        )

        state_machine = sfn.StateMachine(
            self,
            "CreateMarketClone",
            # .next(
            #     tasks.LambdaInvoke(
            #         self,
            #         "GenerateFaucetWalletTask",
            #         lambda_function=generate_faucet_wallet_function,
            #     )
            # )
            definition=tasks.LambdaInvoke(
                self,
                "GenerateFaucetWalletTask",
                lambda_function=generate_faucet_wallet_function,
            ).next(
                tasks.LambdaInvoke(
                    self,
                    "GenerateIssuers",
                    input_path="$.Payload",
                    lambda_function=generate_issuers_function,
                    result_selector={"issuers.$": "$.Payload.issuers"},
                    # result_path="$.issuers",
                    # output_path="$.Payload.issuers",
                )
            )
            # .next(
            #     tasks.LambdaInvoke(
            #         self,
            #         "GenerateFaucetWalletTask",
            #         lambda_function=generate_faucet_wallet_function,
            #     )
            # )
            .next(
                tasks.LambdaInvoke(
                    self,
                    "GrabOrderBookTask",
                    lambda_function=grab_order_book_function,
                    result_path="$.orders",
                    result_selector={
                        "work.$": "$.Payload.distinct_accounts",
                    },
                )
            )
            .next(
                sfn.Map(
                    self,
                    "GenerateOrderWallets",
                    # not relevant with output_path changed above
                    items_path="$.work",
                    # parameters={
                    #     "issuers.$": "$.issuers",
                    #     "work.$": "$.orders.work",
                    # },
                    # works pretty good with the faucet endpoint, this is also
                    # the expected max txns the faucet can put in a single
                    # ledger
                    max_concurrency=4,
                    # max_concurrency=10,
                    # CRAZZZY
                    # max_concurrency=30,
                    # does this work?
                    # result_path=sfn.JsonPath.DISCARD,
                    # result_path="$.issuers",
                    result_selector={
                        "issuers.$": "$.issuers"
                    },
                    output_path="$.issuers",
                ).iterator(
                    tasks.LambdaInvoke(
                        self,
                        "GenerateOrderWalletFromFaucet",
                        lambda_function=generate_faucet_wallet_function,
                        # parameters=
                        result_path="$.wallet",
                        result_selector={
                            "seed.$": "$.Payload.seed",
                            "account.$": "$.Payload.account",
                        },
                    )
                    .next(
                        tasks.LambdaInvoke(
                            self,
                            "GenerateOrdersFromState",
                            lambda_function=generate_orders_function,
                        )
                    )
                    .next(sfn.Succeed(self, "FaucetAccountCreated"))
                )
            )
            .next(sfn.Succeed(self, "CreatedMarket")),
        )
