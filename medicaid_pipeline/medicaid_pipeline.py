from aws_cdk import (
    Stack,
    Environment,
)
from constructs import Construct
from aws_cdk.pipelines import CodePipeline, CodePipelineSource, ShellStep
from medicaid_stage.medicaid_stage import MediciaidPipelineStage


class MedicaidPipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        pipeline = CodePipeline(self, 
                                "MODMedicaidPipeline",
                                pipeline_name="MODMedicaidPipeline",
                                synth=ShellStep("Synth",
                                                input=CodePipelineSource.connection(repo_string="SaiTejaVarasiDev/modmedicaid-aws-codepipeline",branch="main",connection_arn="arn:aws:codeconnections:ap-south-1:443370714691:connection/8b2ccefc-6bdc-442b-8c7c-5d26f632a991"),
                                commands=["npm install -g aws-cdk",
                                          "python -m pip install -r requirements.txt",
                                          "cdk synth",
                                        #   "mkdir -p common/python/lib/python3.11/site-packages",
                                        #   "ls",
                                        #   "pip install -r lambda/requirements.txt --target common/python/lib/python3.11/site-packages",
                                        #   "cd common",
                                        #   "pwd",
                                        #   "zip python.zip python",
                                        #   "cd ..",
                                        #   "cd common/python/lib/python3.11/site-packages",
                                        #   "ls",
                                        #   "pwd",
                                        #   "cd ../../../../.."
                                          ]
                                )
                                
                                )
        
        pipeline.add_stage(MediciaidPipelineStage(self, "dev"
                                        #  env=Environment()
                                        ))