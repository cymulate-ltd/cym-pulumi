import pulumi
from pulumi_aws import autoscaling

class ASG(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:ec2:asg', name, None, opts)
        self.name = name

    def create(self, env: str, launch_template_id, launch_template_version, args: dict):
        args['capacity_rebalance'] = args.get('capacity_rebalance', True)
        args['wait_for_capacity_timeout'] = args.get('wait_for_capacity_timeout', '12m')
        args['suspended_processes'] = args.get('suspended_processes', ['AZRebalance'])
        args['ec2_on_demand_base_capacity'] = args.get('ec2_on_demand_base_capacity', 0)
        args['mixed_instances_policy']['launch_template'] = args['mixed_instances_policy'].get('launch_template', {})
        args['mixed_instances_policy']['launch_template']['overrides'] = args['mixed_instances_policy']['launch_template'].get('overrides', [])
        args['mixed_instances_policy']['instances_distribution'] = args['mixed_instances_policy'].get('instances_distribution', {})
        args['mixed_instances_policy']['instances_distribution']['ec2_on_demand_base_capacity'] = args['mixed_instances_policy']['instances_distribution'].get('ec2_on_demand_base_capacity', 0)
        args['mixed_instances_policy']['instances_distribution']['ec2_on_demand_percentage_above_base_capacity'] = args['mixed_instances_policy']['instances_distribution'].get('ec2_on_demand_percentage_above_base_capacity', 100)
        
        tags = {
            "Name": self.name,
            "node_group_type": "unmanaged",
            "k8s.io/cluster-autoscaler/enabled": "true",
            f"k8s.io/cluster-autoscaler/eks-{env}": "true",
            "k8s.io/cluster-autoscaler/node-template/label/nodeGroup": args['name'],
            f"k8s.io/cluster-autoscaler/node-template/taint/{args['taint'].split(':')[0]}": args['taint'].split(':')[1]
        }

        asg = autoscaling.Group(args['name'],
            name=args['name'],
            capacity_rebalance=args['capacity_rebalance'],
            desired_capacity=args['desired_capacity'],
            max_size=args['max_size'],
            min_size=args['min_size'],
            vpc_zone_identifier=args['vpc_zone_identifier'],
            wait_for_capacity_timeout=args['wait_for_capacity_timeout'],
            suspended_processes=args['suspended_processes'],

            mixed_instances_policy=autoscaling.GroupMixedInstancesPolicyArgs(
                launch_template=autoscaling.GroupMixedInstancesPolicyLaunchTemplateArgs(
                    launch_template_specification=autoscaling.GroupMixedInstancesPolicyLaunchTemplateLaunchTemplateSpecificationArgs(
                        launch_template_id=launch_template_id,
                        version=launch_template_version
                    ),
                    overrides=[autoscaling.GroupMixedInstancesPolicyLaunchTemplateOverrideArgs(
                        instance_type=override['instance_type']
                    ) for override in args['mixed_instances_policy']['launch_template']['overrides']]
                ),
                instances_distribution=autoscaling.GroupMixedInstancesPolicyInstancesDistributionArgs(
                    on_demand_base_capacity=args['mixed_instances_policy']['instances_distribution']['ec2_on_demand_base_capacity'],
                    on_demand_percentage_above_base_capacity=args['mixed_instances_policy']['instances_distribution']['ec2_on_demand_percentage_above_base_capacity'],
                    spot_allocation_strategy="capacity-optimized"
                )
            ),
            tags=[
                autoscaling.GroupTagArgs(
                    key=tag_key,
                    value=tag_value,
                    propagate_at_launch=True,
                ) for tag_key, tag_value in tags.items()
            ],
            opts=pulumi.ResourceOptions(parent=self, ignore_changes=["desiredCapacity"])
        )

        return asg