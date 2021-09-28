from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks

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

        # The code that defines your stack goes here

        generate_issuers_function = lambda_.Function(
            self,
            "MyLambdaFunction",
            code=lambda_.Code.from_asset(
                "functions/generate_issuers/",
                bundling=bundle_python_function_with_requirements,
            ),
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="function.handler",
            timeout=cdk.Duration.seconds(60),
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
            timeout=cdk.Duration.seconds(600),
            memory_size=512,
        )


        state_machine = sfn.StateMachine(
            self,
            "MyStateMachine",
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
                    result_selector={
                        "issuers.$": "$.Payload.issuers"
                    },
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
                    # input_path="$.Payload",
                    # result_path="$.Payload",
                    result_path="$.orders",
                    result_selector={
                        "work.$": "$.Payload.distinct_accounts",
                    },
                    output_path="$.orders",
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
                    max_concurrency=10,
                    # CRAZZZY
                    # max_concurrency=30,
                    # does this work?
                    result_path=sfn.JsonPath.DISCARD,
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
            .next(sfn.Succeed(self, "GreetedWorld")),
        )
