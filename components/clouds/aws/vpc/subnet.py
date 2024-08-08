import pulumi
from pulumi_aws import ec2
from utils.shared import GlobalUtils

class Subnet(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:vpc:subnet', name, None, opts)
        self.name = name

    def create(self, env: str, vpc_id: str, subnets_args: dict):
        subnets = []
        for subnet_key in subnets_args.keys():
            subnet = subnets_args[subnet_key]
            _subnet = ec2.Subnet(subnet['name'],
                vpc_id=vpc_id,
                cidr_block=subnet['cidr_block'],
                availability_zone=subnet['availability_zone'],
                map_public_ip_on_launch=subnet.get('map_public_ip_on_launch', False),
                tags=GlobalUtils.get_global_tags(env, {
                    "Name": subnet['name'],
                }),
                opts=pulumi.ResourceOptions(parent=self)
            )

            subnets.append({
                'id': _subnet.id,
                'name': subnet['name'],
                'public_subnet': subnet['public_subnet']
            })

        return subnets