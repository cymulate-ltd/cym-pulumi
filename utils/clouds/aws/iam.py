from components.clouds.aws.iam import IAM
from utils.clouds.aws.eks.eks import EKSUtils
from utils.shared import GlobalUtils
import pulumi_aws as aws

class IAMUtils:

    @staticmethod
    def iam_handler(iam: IAM, iam_dict: dict):
        visited: dict = {}
        policies_dict: dict = {}
        if iam_dict.get('policies'):
            for policy in iam_dict['policies'].keys():
                policy_dict = iam_dict['policies'][policy]
                _policy = iam.create_policy(policy_name=policy_dict['name'], template_path=policy_dict['template_path'], dynamic_data=policy_dict['template_vars'])
                policies_dict[policy_dict['name']] = { 
                    'name': policy_dict['name'],
                    'arn': _policy.arn
                }
        
        if iam_dict.get('roles'):
            for role in iam_dict['roles'].keys():
                role_dict = iam_dict['roles'][role]
                policies_arn = []

                # searching for arns from the newly created policies, if not created (already exist) -> take arn from aws 
                for policy in role_dict['attach_policies']:
                    if policy in policies_dict:
                        policies_arn.append(policies_dict[policy]['arn'])
                    else:
                        if policy in visited:
                            policies_arn.append(visited[policy]['arn'])
                        else:
                            _policy = aws.iam.get_policy(name=policy)
                            policies_arn.append(_policy.arn)
                            # save visited policies to save calls for `aws.iam.get_policy()`
                            visited[policy] = { 'arn': _policy.arn }
                
                if 'template_vars' not in role_dict:
                    role_dict['template_vars'] = {}
                if 'associated_eks_name' in role_dict:
                    oidc_issuer = EKSUtils.get_oidc_issuer(role_dict['associated_eks_name'])
                    role_dict['template_vars']['principal'] = f"arn:aws:iam::{GlobalUtils.config_dict['aws_account']}:oidc-provider/oidc.eks.{GlobalUtils.config_dict['region']}.amazonaws.com/id/{oidc_issuer}"
                    role_dict['template_vars']['action'] = "sts:AssumeRoleWithWebIdentity"
                    role_dict['template_vars']['condition_key'] = f"oidc.eks.{GlobalUtils.config_dict['region']}.amazonaws.com/id/{oidc_issuer}:aud"
                    role_dict['template_vars']['condition_value'] = "sts.amazonaws.com"
                
                if 'template_path' not in role_dict:
                    role_dict['template_path'] = 'templates/clouds/aws/iam/assume_role_policy.j2'
                iam.create_role(role_name=role_dict['name'], policy_names=role_dict['attach_policies'], policy_arns=policies_arn, template_path=role_dict['template_path'], dynamic_data=role_dict['template_vars'])