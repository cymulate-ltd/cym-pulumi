## Install

Run the command:
```
curl -fsSL https://get.pulumi.com | sh
```

## Login to pulumi

```
pulumi login
```

## Install pulumi dependencies

install python3-venv: 
```
apt install python3-venv
```

create venv:
```
python3 -m venv venv
```

activate venv:
```
source venv/bin/activate
```

install requirements with pip inside venv:
```
pip3 install -r requirements.txt
```

# Setup pulumi project
## Deploying and running the program

1.  Create a new stack:
    ```bash
    pulumi stack init <stack name> --secrets-provider="awskms://alias/pulumi?region=us-east-1"
    ```

2.  Run `pulumi up` to preview and deploy changes:
    ```
    pulumi preview --diff
    pulumi up --diff -s <stack name | or leave empty>
    ```

## Show output secrets
```
Run `pulumi stack output --show-secrets`
```

# Pulumi code structure
This project is built with the concept of layers.
In each folder there should be a pulumi.yaml file which will create a stack with a relative path.
Each pulumi project should have a config.yaml file that will inherit all parent folder config.yaml files.
This way we can create resources based on logic level.
For example: In `regions/us-east-1` there will be a config.yaml file that will be responsible for region type resources.
and under `regions/us-east-1/envs/stg` there will resources such as elasticache, s3 or any related resources for this environment.

In each "project" there is a built in support for a config folder that inside you can create those files:
`sg_config.yaml` and `iam_config.yaml` this will allow us to gather all iams and sgs in one place and load them before any other resource.

## Clean up

1.  Run `pulumi destroy` to tear down all resources.

2.  To delete the stack itself, run `pulumi stack rm`. Note that this command deletes all deployment history from the Pulumi console.

# Overriding reources
## Code approach

in order to adopt existing resources we need to hard code the parameter `import_` so pulumi will recoginze that resource without causing an error
for example:
```
policy = iam.Policy(policy_name, name=policy_name,
    policy=Output.all(dynamic_data).apply(lambda args: policy_template.render(args[0])),
    opts=pulumi.ResourceOptions(parent=self,import_="arn:aws:iam::<account-number>:policy/xxxxxxxxxx")
)
```
then run:
```
$ pulumi up -s <env>
```
and then remove `,import_="arn:aws:iam::<account-number>:policy/xxxxxxxxxx"`

## CLI approach
Another option is to use pulumi import:
```
pulumi import <resource name>

for example (cloudfront distribution):
pulumi import aws:cloudfront/distribution:Distribution distribution XXXXXX
```

# Migrating resources between stacks
in order to migrate resources between stacks you will need to remove it from the first stack and then import it to the desired stack.

```
pulumi stack --show-urns

pulumi state delete -s <stack-name> "<urn>" (make sure to wrap with quotes and add \ at any $ sign occurance)
```

import the resources to the new stack
```
pulumi import --protect=false --parent <urn> <resource name> <aws resource arn>

for example (cloudfront distribution):
pulumi import --protect=false --parent urn:pulumi:us-east-1::cymulate::cymulate:utils:cloudtrail::us-east-1 aws:cloudtrail/trail:Trail management-events arn:aws:cloudtrail:us-east-1:<account-number>:trail/management-events
```

## migrate stack name
In order to change stack name run the command:
pulumi stack rename <new-stack-name>

In order to change path in s3 (backend.url in Pulumi.yaml) copy the relevant stack from s3 to a new dir and update in Pulumi.yaml

# More on
* https://www.pulumi.com/docs/using-pulumi/organizing-projects-stacks/
* https://www.pulumi.com/docs/concepts/config/
* https://www.youtube.com/watch?v=60LYNRnmM5M (https://github.com/kevanpeters/Intro_pulumi/blob/master)
