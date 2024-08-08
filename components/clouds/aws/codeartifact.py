
import pulumi
from pulumi import Output
from pulumi_aws import codeartifact

class CodeArtifact(pulumi.ComponentResource):

    def __init__(self, name, opts = None):
        super().__init__('cymulate:utils:codeartifact', name, None, opts)

    def create_repository(self, args: dict):
        repository = codeartifact.Repository(args['repo_name'],
            repository=args['repo_name'],
            domain=args['domain'],
            description=args['description'],
            opts=pulumi.ResourceOptions(parent=self)
        )