import pulumi
from pulumi_aws import eks, ec2
from utils.shared import GlobalUtils
from components.clouds.aws.ec2.sg import SG
from components.clouds.aws.ec2.asg import ASG
from components.clouds.aws.ec2.launch_template import LaunchTemplate

class NodeGroup(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:eks:nodegroup', name, None, opts)
        self.name = name

    def create(self, env: str, cluster_name: str, node_role_arn, instance_profile_arn, args: dict) -> None:
        lt = LaunchTemplate(self.name, opts=pulumi.ResourceOptions(parent=self))

        lt_args = args['launch_template']
        lt_args['node_group_type'] = args['node_group_type']
        lt_args['user_data']['node_group'] = args['eks_node_group']
        lt_args['user_data']['taint'] = args.get('taint', "")
        lt_args['user_data']['component_type'] = 'worker'
        lt_args['user_data']['environment'] = env
        lt_args['user_data']['enable_docker_bridge'] = args.get('enable_docker_bridge', "")

        sg_ids = [GlobalUtils.cache_dict['security_group'][f'{args["name"]}-sg']['id'], GlobalUtils.cache_dict['security_group'][f'eks-worker-node-sg-{env}']['id']]
        launch_template: ec2.LaunchTemplate = lt.create(
            env=env,
            instance_profile_arn=instance_profile_arn,
            security_group_ids=sg_ids,
            args=lt_args
        )

        node_group_type = args['node_group_type']
        # For unmanaged node groups -> create auto-scaling-group
        if node_group_type == "unmanaged":
            asg = ASG(self.name, opts=pulumi.ResourceOptions(parent=self))
            asg.create(env, launch_template.id, launch_template.latest_version, args)
        
        # For managed node groups
        elif node_group_type == "managed":
            eks.NodeGroup(args['name'],
                node_group_name=args['name'],
                cluster_name=cluster_name,
                node_role_arn=node_role_arn,
                subnet_ids=args['subnet_ids'],
                capacity_type=args['capacity_type'],
                scaling_config=eks.NodeGroupScalingConfigArgs(
                    desired_size=args['scaling_config']['desired_size'],
                    max_size=args['scaling_config']['max_size'],
                    min_size=args['scaling_config']['min_size']
                ),
                launch_template=eks.NodeGroupLaunchTemplateArgs(
                    id=launch_template.id,
                    version=launch_template.latest_version
                ),
                tags=GlobalUtils.get_global_tags(env, {
                    "Name": args['name'],
                    "node_group_type": "managed",
                    f"kubernetes.io/cluster/eks-{env}": "owned"
                }),
                opts=pulumi.ResourceOptions(parent=self,
                    ignore_changes=["scalingConfig.desiredSize"],
                    custom_timeouts=pulumi.CustomTimeouts(create='2h', update='4h', delete='30m')
                )
            )
    