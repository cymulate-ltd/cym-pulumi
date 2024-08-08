import pulumi
from pulumi_aws import ec2
from utils.shared import GlobalUtils

class VPC(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:vpc', name, None, opts)
        self.name = name

    def create(self, env: str, name: str, default_cidr_block: list, extra_cidr_blocks: list = []):
        vpc = ec2.Vpc(name,
            cidr_block=default_cidr_block,
            instance_tenancy="default",
            tags=GlobalUtils.get_global_tags(env, {
                "Name": name,
            }),
            opts=pulumi.ResourceOptions(parent=self)
        )

        for index, cidr_block in enumerate(extra_cidr_blocks):
            ec2.VpcIpv4CidrBlockAssociation(f'{self.name}-{index}',
                vpc_id=vpc.id,
                cidr_block=cidr_block,
                opts=pulumi.ResourceOptions(parent=self)
            )

        return vpc.id