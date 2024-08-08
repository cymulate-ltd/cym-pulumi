
import pulumi
from pulumi import Input, InputType
from pulumi_aws import ec2
from typing import Sequence
from typing import Literal
from utils.shared import GlobalUtils

class SG(pulumi.ComponentResource):

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:ec2:sg', name, None, opts)
    
    @staticmethod
    def get_sg_by_name(
        name: str,
        vpc_id: str
    ) -> ec2.AwaitableGetSecurityGroupResult:
        sg = None
        try:
            sg = ec2.get_security_group(name=name, vpc_id=vpc_id)
            return sg.id
        except Exception as e:
            raise Exception(e)
    
    def create(self, 
        name: str,
        env: str,
        vpc_id: str,
        description: str = '',
        ingress_rules: Input[Sequence[Input[InputType[ec2.SecurityGroupIngressArgs]]]] = None,
        egress_rules: Input[Sequence[Input[InputType[ec2.SecurityGroupEgressArgs]]]] = None,
        ignore_changes: bool = False,
        extra_tags: dict = {},
        opts = None
    ) -> ec2.SecurityGroup:
        ignore_list=[]
        if ignore_changes:
            ignore_list=['ingress', 'egress']

        sg = ec2.SecurityGroup(name,
            name=name,
            description=description,
            vpc_id=vpc_id,
            ingress=ingress_rules,
            egress=egress_rules,
            tags=GlobalUtils.get_global_tags(env, { 'Name': name, **extra_tags }),
            opts=opts if opts else pulumi.ResourceOptions(parent=self, ignore_changes=ignore_list)
        )

        return sg

    def get_sg_rule(self,
            type: Literal['ingress', 'egress'],
            description: str,
            from_port: int,
            to_port: int,
            protocol: str = 'tcp',
            security_group_ids: Sequence[str] = None,
            cidr_blocks: Sequence[str] = None,
            ipv6_cidr_blocks: Sequence[str] = None
    ):
        if not cidr_blocks and not ipv6_cidr_blocks and not security_group_ids:
            raise Exception('Missing cidr_blocks and ipv6_cidr_blocks and security_groups_ids, choose one!')
        elif (cidr_blocks and security_group_ids) or (ipv6_cidr_blocks and security_group_ids) or (cidr_blocks and ipv6_cidr_blocks):
            raise Exception('Both (cidr_blocks and security_groups_ids) or (ipv6_cidr_blocks and security_group_ids) or (cidr_blocks and ipv6_cidr_blocks) specified, choose one!')
        
        if type == 'ingress':
            sg_rule = ec2.SecurityGroupIngressArgs(
                description=description,
                from_port=from_port,
                to_port=to_port,
                protocol=protocol
            )
        elif type == 'egress':
            sg_rule = ec2.SecurityGroupEgressArgs(
                description=description,
                from_port=from_port,
                to_port=to_port,
                protocol=protocol
            )

        if security_group_ids:
            sg_rule.security_groups = security_group_ids
        elif cidr_blocks:
            sg_rule.cidr_blocks = cidr_blocks
        elif ipv6_cidr_blocks:
            sg_rule.ipv6_cidr_blocks = ipv6_cidr_blocks
        else:
            raise Exception('Must specify destination!')

        return sg_rule