import pulumi, os, jinja2
from pulumi import Output
from pulumi_aws import kms
from utils.shared import GlobalUtils

class KMS(pulumi.ComponentResource):

    def __init__(self,name, opts=None):
        super().__init__('cymulate:utils:kms', name, None, opts)
        self.name = name

    def create_kms_key(self, kms_key_id, description = None, tags = None):
        key_props = {}
        if description:
            key_props["description"] = description
        if tags:
            key_props["tags"] = tags  
        
        kms_key = kms.Key(resource_name=kms_key_id,
                          **key_props,
                          opts=pulumi.ResourceOptions(parent=self))
        
        #Creates an alias for the kms key
        kms.Alias(resource_name=kms_key_id,
                  name=f"alias/{kms_key_id}",
                  target_key_id=kms_key.id, 
                  opts=pulumi.ResourceOptions(parent=self))

        return kms_key

    def create_kms_key_policy(self, kms_key_name: str, kms_key_id: str, policy: str):
        kms.KeyPolicy(resource_name=kms_key_name,
                      key_id=kms_key_id,
                      policy=policy,
                      opts=pulumi.ResourceOptions(parent=self))
    
    def get_kms_key(self, kms_key_id: str):
        return kms.get_key(key_id=kms_key_id)

