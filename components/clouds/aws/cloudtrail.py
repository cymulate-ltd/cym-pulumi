import sys; sys.path.append('../../../../')
import pulumi,os ,json, jinja2
from components.clouds.aws.kms import KMS
from pulumi_aws import cloudtrail

class Cloudtrail(pulumi.ComponentResource):

    name: str
    dir_path = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, name, opts = None):
        super().__init__('cymulate:utils:cloudtrail', name, None, opts)
        
        self.name = name
    
    def create_trail(self, trail_name: str, s3_bucket: str, kms_key: str, multi_regional: bool ,account: str, region: str) -> None:

        kms = KMS(name=kms_key)

        key = kms.create_kms_key(kms_key_id=kms_key)
        key_id = key.id.apply(lambda id: id)
        key_arn = key.arn.apply(lambda arn: arn)
        
        with open(f"{self.dir_path}/../../../templates/clouds/aws/kms/kms_cloudtrail_policy.j2",mode="r") as file:
          policy_template = jinja2.Template(file.read())

        policy = policy_template.render({"trail_name":  trail_name,
                                    "account": account,
                                    "region": region})

        kms.create_kms_key_policy(kms_key_name=kms_key,
                                  kms_key_id=key_id,
                                  policy=policy)

        cloudtrail.Trail(resource_name=trail_name,
                        name=trail_name,
                        s3_bucket_name=s3_bucket,
                        kms_key_id=key_arn,
                        is_multi_region_trail=multi_regional,
                        opts=pulumi.ResourceOptions(parent=self)
                    )

        
