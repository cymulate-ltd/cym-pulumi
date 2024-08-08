
import pulumi, json
from pulumi import Output
import pulumi_aws as aws
from pulumi_aws import secretsmanager
from pulumi_aws.secretsmanager import AwaitableGetSecretVersionResult

class SecretManager(pulumi.ComponentResource):

    def __init__(self, name, opts=None):
        super().__init__('cymulate:utils:secretmanager', name, None, opts)

    def get_secret_value(self, secret_arn: str):
        secret: AwaitableGetSecretVersionResult = secretsmanager.get_secret_version(
            secret_id=secret_arn)
        
        return secret.secret_string

    def create_json_secret(self, name, json_secret_value: str, update_dict: dict = {}) -> str:
        """
        Creates secret json

        :param str name: The name of the created secret.
        :param str json_secret_value: Json value of the new secret.
        :param str update_dict (Optional): A dict of key / values that will update the json_secret_value accordingly.
        """
        
        aws_config = pulumi.Config("aws")
        aws_region = aws_config.require("region")
        provider = None

        if aws_region != 'us-east-1':
            provider = aws.Provider("useast1", region="us-east-1")

        json_secret = json.loads(json_secret_value)

        for key, value in update_dict.items():
            json_secret[key] = value
        
        # Create secret
        secret = secretsmanager.Secret(
            name, name=name, opts=pulumi.ResourceOptions(parent=self, provider=provider))
        # Create secret version
        secretsmanager.SecretVersion(name,
                                     secret_id=secret.id,
                                     secret_string=json.dumps(json_secret, indent=4),
                                     opts=pulumi.ResourceOptions(parent=self, provider=provider, ignore_changes=["secretString"])
                                     )
        
        return secret.arn
    
    def create_json_secret_from_output(self, name, output_json_str: Output[str], kms_key_id = None, create_secret_in_region = False, tags = None) -> str:
        """
        Creates secret json

        :param str name: The name of the created secret.
        :param str output_json_str: Output json value of the new secret.
        """
        
        aws_config = pulumi.Config("aws")
        aws_region = aws_config.require("region")
        provider = None

        if aws_region != 'us-east-1' and not create_secret_in_region:
            provider = aws.Provider("useast1", region="us-east-1")
        
        secret_props = {}
        if kms_key_id:
            secret_props["kms_key_id"] = kms_key_id
        if tags:
            secret_props["tags"] = tags

        # Create secret
        secret = secretsmanager.Secret(
            name, name=name, **secret_props, opts=pulumi.ResourceOptions(parent=self, provider=provider))

        # Create secret version
        secretsmanager.SecretVersion(name,
                                     secret_id=secret.id,
                                     secret_string=output_json_str.apply(lambda x: x),
                                     opts=pulumi.ResourceOptions(parent=self, provider=provider, ignore_changes=["secretString"])
                                     )
        
        return secret.arn
