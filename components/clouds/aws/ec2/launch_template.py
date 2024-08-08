import pulumi, os, jinja2, base64
from pulumi_aws import ec2
from utils.shared import GlobalUtils

class LaunchTemplate(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:ec2:launch_template', name, None, opts)
        self.name = name

    def create(self, env: str, instance_profile_arn, security_group_ids: list, args: dict) -> ec2.LaunchTemplate:
        args['update_default_version'] = args.get('update_default_version', True)
        args['block_device_mappings']['ebs']['volume_type'] = args['block_device_mappings']['ebs'].get('volume_type', 'gp3')
        args['block_device_mappings']['ebs']['encrypted'] = args['block_device_mappings']['ebs'].get('encrypted', "true")
        args['block_device_mappings']['device_name'] = args['block_device_mappings'].get('device_name', '/dev/xvda')
        
        launch_template_params = {}
        if args['node_group_type'] == "unmanaged":
            launch_template_params['iam_instance_profile'] = ec2.LaunchTemplateIamInstanceProfileArgs(
                arn=instance_profile_arn
            )
        if 'metadata_options' in args:
            launch_template_params['metadata_options'] = ec2.LaunchTemplateMetadataOptionsArgs(
                http_endpoint=args['metadata_options']['http_endpoint'],
                http_tokens=args['metadata_options']['http_tokens']
            )
        else:
            launch_template_params['metadata_options'] = ec2.LaunchTemplateMetadataOptionsArgs(
                http_endpoint=None,
                http_tokens=None
            )
        
        common_tags = GlobalUtils.get_global_tags(env, {
            "Name": args['name'],
            f"kubernetes.io/cluster/eks-{env}": "owned"
        })
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(f"{dir_path}/../../../../templates/clouds/aws/eks/launch_template/user_data.j2",mode="r") as file:
            user_data = jinja2.Template(file.read())

        user_data_rendered = pulumi.Output.all(args['user_data']).apply(
            lambda args: user_data.render(args[0])
        )

        user_data_rendered = user_data_rendered.apply(lambda user_data: str(base64.b64encode(bytes(user_data.replace("\r\n", "\n"), 'utf-8')).decode("utf-8")))

        launch_template = ec2.LaunchTemplate(f"{args['name']}-launch-template",
            name=f"{args['name']}-launch-template",
            image_id=args['ami_id'],
            instance_type=args['instance_type'],
            update_default_version=args['update_default_version'],
            key_name=args['key_name'],
            user_data=user_data_rendered,
            block_device_mappings=[ec2.LaunchTemplateBlockDeviceMappingArgs(
                device_name=args['block_device_mappings']['device_name'],
                ebs=ec2.LaunchTemplateBlockDeviceMappingEbsArgs(
                    encrypted=args['block_device_mappings']['ebs']['encrypted'],
                    volume_size=args['block_device_mappings']['ebs']['volume_size'],
                    volume_type=args['block_device_mappings']['ebs']['volume_type'],
                )
            )],
            network_interfaces=[ec2.LaunchTemplateNetworkInterfaceArgs(
                associate_public_ip_address=args['network_interfaces']['public_ip'],
                security_groups=security_group_ids
            )],
            tag_specifications=[ec2.LaunchTemplateTagSpecificationArgs(
                    resource_type="instance",
                    tags=common_tags
                ), ec2.LaunchTemplateTagSpecificationArgs(
                    resource_type="volume",
                    tags=common_tags
                )
            ],
            **launch_template_params,
            tags=common_tags,
            opts=pulumi.ResourceOptions(parent=self,ignore_changes=['metadataOptions'])
        )

        return launch_template