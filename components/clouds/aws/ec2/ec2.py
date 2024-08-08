import pulumi
from pulumi_aws import ec2
from pulumi_aws import iam
from utils.shared import GlobalUtils
from components.clouds.aws.ec2.sg import SG
from components.clouds.aws.iam import IAM

class Ec2(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:ec2:instance', name, None, opts)
        self.name = name

    def create(self, env: str, args: dict):
        _iam = IAM(name=args['name'])
        policy_names = []

        for policy_arn in args['iam_policies_attachment']:
            policy_names.append(policy_arn.split('/')[-1])
            
        role: iam.Role = _iam.create_role(
            role_name=f'{args["name"]}-role',
            policy_names=policy_names,
            policy_arns=args['iam_policies_attachment'],
            template_path='templates/clouds/aws/iam/ec2/assume_role.j2'
        )

        instance_profile_role = _iam.create_instance_profile(name=f'{args["name"]}-profile', role_name=role.name)

        vpc_security_group_ids = []
        for sg_id in args['vpc_security_groups']:
            vpc_security_group_ids.append(sg_id)

        instance = ec2.Instance(args['name'],
            ami=args['ami_id'],
            associate_public_ip_address=args.get('associate_public_ip_address', False),
            instance_type=args['instance_type'],
            subnet_id=args['subnet_id'],
            vpc_security_group_ids=vpc_security_group_ids,
            iam_instance_profile=instance_profile_role.name,
            key_name=args.get('key_name', f"{env}-key"),
            get_password_data=args.get('get_password_data', False),
            root_block_device=ec2.InstanceRootBlockDeviceArgs(
                delete_on_termination=args['ebs'].get('delete_on_termination', True),
                encrypted=args['ebs'].get('encrypted', True),
                volume_type=args['ebs']['volume_type'],
                volume_size=args['ebs']['volume_size'],
                tags=GlobalUtils.get_global_tags(env, {
                    "Name": args['name'],
                })
            ),
            metadata_options=ec2.InstanceMetadataOptionsArgs(
                http_endpoint=args['metadata_options'].get('http_endpoint', 'enabled'),
                http_tokens=args['metadata_options'].get('http_tokens', 'required')
            ),
            tags=GlobalUtils.get_global_tags(env, {
                "Name": args['name'],
            }),
            opts=pulumi.ResourceOptions(parent=self)
        )

        if args['public_eip'] == True:
            eip: ec2.Eip = self.create_elastic_ip(env=env, name=args['name'])
            ec2.EipAssociation(f'{args["name"]}-assoc',
                instance_id=instance.id,
                allocation_id=eip.allocation_id,
                opts=pulumi.ResourceOptions(parent=self)
            )

        return instance.id

    def create_elastic_ip(self, env: str, name: str):
        eip = ec2.Eip(
            name,
            domain="vpc",
            tags=GlobalUtils.get_global_tags(env, {
                "Name": name,
            }),
            opts=pulumi.ResourceOptions(parent=self)
        )
        return eip
    