
import pulumi, jinja2, os
from pulumi import Output
from pulumi_aws import iam, eks
from utils.shared import GlobalUtils

class IAM(pulumi.ComponentResource):

    name: str
    
    def __init__(self, name, opts = None):
        super().__init__('cymulate:utils:iam', name, None, opts)

        self.name = name

    def create_policy(self, policy_name: str, template_path: str, dynamic_data: dict = {}, description: str = ""):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        policy_template = jinja2.Template(open(f"{dir_path}/../../../{template_path}").read())
        policy = iam.Policy(policy_name, 
            name=policy_name,
            policy=Output.all(dynamic_data).apply(lambda args: policy_template.render(args[0])),
            description=description,
            opts=pulumi.ResourceOptions(parent=self)
        )

        return policy

    def create_role(self, role_name: str, policy_names: list, policy_arns: list, dynamic_data: dict = {}, template_path: str = 'templates/clouds/aws/iam/assume_role_policy.j2') -> iam.Role:
        dir_path = os.path.dirname(os.path.realpath(__file__))        
        role_template = jinja2.Template(open(f"{dir_path}/../../../{template_path}").read())
        role = iam.Role(role_name, 
            name=role_name,
            assume_role_policy=Output.all(dynamic_data).apply(lambda args: role_template.render(args[0])),
            opts=pulumi.ResourceOptions(parent=self)
        )

        for index, policy_arn in enumerate(policy_arns):
            iam.RolePolicyAttachment(f'{role_name}-{policy_names[index]}',
                role=role.name,
                policy_arn=policy_arn,
                opts=pulumi.ResourceOptions(parent=self)
            )

        return role

    def create_instance_profile(self, name: str, role_name: str):
        iam_instance_profile = iam.InstanceProfile(name,
            name=name,
            role=role_name,
            tags={ "Name": name },
            opts=pulumi.ResourceOptions(parent=self)
        )

        return iam_instance_profile
    
    def create_iam_openid_connect_provider(self, name: str, url: str, client_id_lists: list, thumbprint_lists: list):
        oidc = iam.OpenIdConnectProvider(name,
            url=url,
            client_id_lists=client_id_lists,
            thumbprint_lists=thumbprint_lists,
            opts=pulumi.ResourceOptions(parent=self)
        )
        return oidc.arn

    # def secretmanager_access_role(self, role_name: str, policy_name: str, eks_cluster_name: str, secret_arn: pulumi.Output[str], region: str, template_path: str, account: str = '<account-number>'):
    #     eks_cluster = eks.get_cluster(name=eks_cluster_name)
    #     oidc_issuer = eks_cluster.identities[0].oidcs[0].issuer
    #     # Extracts `{issuer}` from `https://oidc.eks.us-east-1.amazonaws.com/id/{issuer}`
    #     oidc_issuer = oidc_issuer[oidc_issuer.rfind('/')+1:]
        
    #     dir_path = os.path.dirname(os.path.realpath(__file__))
    #     policy_template = jinja2.Template(open(f"{dir_path}/../../../templates/clouds/aws/{template_path}").read())
    #     dynamic_data = { "resource_arn": secret_arn }
        
    #     policy = iam.Policy(policy_name, name=policy_name,
    #         policy=Output.all(dynamic_data).apply(lambda args: policy_template.render(args[0])),
    #         opts=pulumi.ResourceOptions(parent=self)
    #     )
        
    #     role_template = jinja2.Template(open(f"{dir_path}/../../../templates/clouds/aws/iam/assume_role_policy.j2").read())
    #     dynamic_data = {
    #         'principal': f'arn:aws:iam::{account}:oidc-provider/oidc.eks.{region}.amazonaws.com/id/{oidc_issuer}',
    #         'action': 'sts:AssumeRoleWithWebIdentity',
    #         'condition_key': f'oidc.eks.{region}.amazonaws.com/id/{oidc_issuer}:aud',
    #         'condition_value': 'sts.amazonaws.com'
    #     }
    #     role = iam.Role(role_name, name=role_name, opts=pulumi.ResourceOptions(parent=self),
    #         assume_role_policy=Output.all(dynamic_data).apply(lambda args: role_template.render(args[0]))
    #     )

    #     iam.RolePolicyAttachment(role_name,
    #         role=role.name,
    #         policy_arn=policy.arn,
    #         opts=pulumi.ResourceOptions(parent=self)
    #     )

