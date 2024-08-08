import sys; sys.path.append('../../../../')

import pulumi, os
from pulumi_aws import ec2
from utils.shared import GlobalUtils

class KeyPair(pulumi.ComponentResource):

    name: str
    dir_path = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, name, opts = None):
        super().__init__('cymulate:utils:ec2:key-pair', name, None, opts)

        self.name = name
    
    def create(self, env: str, rsa_public_key: str):
        name = self.name
        keypair = ec2.KeyPair(name,
            key_name=name,
            public_key=rsa_public_key,
            tags=GlobalUtils.get_global_tags(env, {
                "Name": name,
            }),
            opts=pulumi.ResourceOptions(parent=self)
        )

        return keypair
