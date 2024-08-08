
import pulumi, os, jinja2
from pulumi import Output
from pulumi_aws import ecr

class ECR(pulumi.ComponentResource):

    name: str
    repository_id: pulumi.Output[str]

    def __init__(self, name, opts = None):
        super().__init__('cymulate:utils:ecr', name, None, opts)

        self.name = name

    def create(self, lifecycle_policy = None):
        # Create a repository
        repository = ecr.Repository(self.name, name=self.name, opts=pulumi.ResourceOptions(parent=self))

        # Create a lifecycle
        if lifecycle_policy:
            policy = lifecycle_policy
        else:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            policy = open(f"{dir_path}/../../../templates/clouds/aws/ecr/lifecycle_policy.j2").read()

        policy_template = jinja2.Template(policy)
        dynamic_data = {}

        ecr.LifecyclePolicy(self.name, 
                            repository=repository.name,
                            policy=Output.all(dynamic_data).apply(lambda args: policy_template.render(args[0])),
                            opts=pulumi.ResourceOptions(parent=self)
                            )

        
        self.repository_id = repository.id
