import sys; sys.path.append('../../../../')
import pulumi, os, jinja2
from components.clouds.aws.kms import KMS
from pulumi_aws import ebs



class EBS(pulumi.ComponentResource):

    name: str
    dir_path = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, name, opts = None):
        super().__init__('cymulate:utils:ebs', name, None, opts)

        self.name = name
    
    def enable_default_encryption(self, enabled: bool, kms_key: str) -> None:
        ebs.EncryptionByDefault(resource_name=kms_key, enabled=enabled, opts=pulumi.ResourceOptions(parent=self))

        kms = KMS(name=kms_key)

        key = kms.get_kms_key(kms_key_id=kms_key)
        key_arn = key.arn

        # with open(f"{self.dir_path}/../../../../templates/clouds/aws/kms/kms_ebs_policy.j2",mode="r") as file:
          # policy_template = jinja2.Template(file.read())

        # policy = policy_template.render({"kms_key":  kms_key,
                                    # "account": account,
                                    # "region": region})
        
        # kms.create_kms_key_policy(kms_key_name=kms_key,
                            # kms_key_id=key_id,
                            # policy=policy)
        
        # Set a default KMS key for the EBS encryption-by-default
        ebs.DefaultKmsKey(resource_name=kms_key, key_arn=key_arn, opts=pulumi.ResourceOptions(parent=self))
