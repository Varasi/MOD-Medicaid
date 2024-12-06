from aws_cdk import (
    Stage,
)
from constructs import Construct
from health_connector_cdk.health_connector_cdk_stack import HealthConnectorCdkStack

class MediciaidPipelineStage(Stage):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        medicaidstack = HealthConnectorCdkStack(self,'MODMediciaidStack')
        