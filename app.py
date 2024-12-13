#!/usr/bin/env python3
import os

import aws_cdk as cdk

from medicaid_pipeline.medicaid_pipeline import MedicaidPipelineStack

app = cdk.App()
MedicaidPipelineStack(app, "MedicaidPipelineStack",

    #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

    env=cdk.Environment(account='443370714691', region='ap-south-1'),
    pipeline_stage_name="dev",
    env_name="dev"
    )

# MedicaidPipelineStack(app, "MedicaidPipelineStack",
#     env=cdk.Environment(account='443370714691', region='ap-south-1'),
#     pipeline_stage_name="test",
#     env_name="test"
#     )

# MedicaidPipelineStack(app, "MedicaidPipelineStack",
#     env=cdk.Environment(account='443370714691', region='ap-south-1'),
#     pipeline_stage_name="prod",
#     env_name="prod"
#     )

app.synth()
