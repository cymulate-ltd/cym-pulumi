import pulumi
from pulumi_aws import ec2
from utils.shared import GlobalUtils

class InternetGatway(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:vpc:igw', name, None, opts)
        self.name = name

    def create(self, env: str, vpc_id: str):
        igw = ec2.InternetGateway(
            self.name,
            vpc_id=vpc_id,
            tags=GlobalUtils.get_global_tags(env, {
                "Name": self.name,
            }),
            opts=pulumi.ResourceOptions(parent=self)
        )
        return igw.id