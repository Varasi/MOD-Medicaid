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
                                                input=CodePipelineSource.connection(repo_string="Varasi/MOD-Medicaid",branch="subdev2",connection_arn="arn:aws:codeconnections:ap-south-1:443370714691:connection/8fb31a33-2f93-4c4f-a057-11803c0579e4"),
                                commands=["npm install -g aws-cdk",
                                        #   "python -m pip install -r requirements.txt",
                                          "cdk synth",
                                          "mkdir common\python\lib\python3.11\site-packages",
                                          "pip install -r lambda\requirements.txt --target common\python\lib\python3.11\site-packages",
                                          "cd common",
                                          "tar.exe -a -cf python.zip python",
                                          "cd .."
                                          ]
                                )
                                
                                )
        
        pipeline.add_stage(MediciaidPipelineStage(self, "dev"
                                        #  env=Environment()
                                        ))