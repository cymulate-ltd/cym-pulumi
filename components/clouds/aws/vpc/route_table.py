import pulumi
from pulumi_aws import ec2
from utils.shared import GlobalUtils

class RouteTable(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:vpc:route-table', name, None, opts)
        self.name = name

    def create(self, env: str, vpc_id: str, subnet_name: str, subnet_id: str, igw_id: str = None, nat_gatway_id: str = None):
        if (not nat_gatway_id and not igw_id) or (nat_gatway_id and igw_id):
            raise Exception('Must pass only one of internet-gateway id or nat-gateway id!')
        
        route_params = {}
        if igw_id:
            route_params['gateway_id'] = igw_id
        elif nat_gatway_id:
            route_params['nat_gateway_id'] = nat_gatway_id

        route_table = ec2.RouteTable(subnet_name,
            vpc_id=vpc_id,
            routes=[
                ec2.RouteTableRouteArgs(
                    cidr_block="0.0.0.0/0",
                    **route_params
                ),
                ec2.RouteTableRouteArgs(
                    ipv6_cidr_block="::/0",
                    **route_params
                )
            ],
            tags=GlobalUtils.get_global_tags(env, {
                "Name": subnet_name,
            }),
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        ec2.RouteTableAssociation(f'{self.name}-assoc',
            subnet_id=subnet_id,
            route_table_id=route_table.id,
            opts=pulumi.ResourceOptions(parent=self)
        )

        return route_table.id
