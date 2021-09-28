from aws_cdk import core as cdk

from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks as tasks

class StepStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hello_function = lambda_.Function(self, "MyLambdaFunction",
                                          code=lambda_.Code.from_inline("""
                                exports.handler = (event, context, callback) = > {
                                    callback(null, "Hello World!");
                                }"""),
                                          runtime=lambda_.Runtime.NODEJS_12_X,
                                          handler="index.handler",
                                          timeout=cdk.Duration.seconds(25))

        state_machine = sfn.StateMachine(self, "MyStateMachine",
                                         definition=tasks.LambdaInvoke(self, "MyLambdaTask",
                                            lambda_function=hello_function).next(
                                            sfn.Succeed(self, "GreetedWorld")))
