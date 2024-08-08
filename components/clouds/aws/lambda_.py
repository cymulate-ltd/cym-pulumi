import pulumi, os
from pulumi_aws import lambda_
from utils.shared import GlobalUtils

class Lambda(pulumi.ComponentResource):

    def __init__(self, name, opts = None):
        super().__init__('cymulate:utils:lambda', name, None, opts)
        self.dir_path = os.path.dirname(os.path.abspath(__file__))

        self.name = name

    def create_function(self, env: str, args: dict, security_groups: list):

        args["name"] = args.get("name", "")
        args["role_name"] = args.get("role_name", "")
        args["image_uri"] = args.get("image_uri", "")
        args["source_file"] = args.get("source_file", "")
        args["handler"] = args.get("handler", "")
        args["runtime"] = args.get("runtime", "")
        args['trigger'] = args.get("trigger", "")
        args['trigger_arn'] = args.get("trigger_arn", "")
        args['trigger_batch_size'] = args.get("trigger_batch_size", 0)
        args['memory_size'] = args.get("memory_size", 0)
        args['reserved_concurrent_executions'] = args.get("reserved_concurrent_executions", 0)
        args['timeout'] = args.get("timeout", 0)
        args["vpc_config"] = args.get("vpc_config", {})
        args["env_vars"] = args.get("env_vars", {})

        # security_group_ids = [sg["security_groups_id"] for sg in args["vpc_config"].get("security_groups_ids", [])]
        subnet_ids = [subnet["subnets_id"] for subnet in args["vpc_config"].get("subnets_ids", [])]


        if args["image_uri"]:
            lambda_function = lambda_.Function(
                args["name"],
                name=args["name"],
                role=args["role_name"],
                package_type="Image",
                image_uri=args["image_uri"],
                timeout=args['timeout'],
                memory_size=args['memory_size'],
                reserved_concurrent_executions=args['reserved_concurrent_executions'],
                vpc_config=lambda_.FunctionVpcConfigArgs(
                    security_group_ids=security_groups,
                    subnet_ids=subnet_ids
                ),
                environment=lambda_.FunctionEnvironmentArgs(
                    variables=args["env_vars"]
                ),
                tags=GlobalUtils.get_global_tags(env, {
                    "Name": args["name"],
                }),
                opts=pulumi.ResourceOptions(parent=self, ignore_changes=['environment','imageUri',"memorySize","timeout","reservedConcurrentExecutions"])
            )
        else:
            lambda_function = lambda_.Function(
                args["name"],
                name=args["name"],
                role=args["role_name"], 
                source_file=args["source_file"],
                handler=args["handler"],
                timeout=args['timeout'],
                memory_size=args['memory_size'],
                reserved_concurrent_executions=args['reserved_concurrent_executions'],
                vpc_config=lambda_.FunctionVpcConfigArgs(
                    security_group_ids=security_group_ids,
                    subnet_ids=subnet_ids
                ),
                environment=lambda_.FunctionEnvironmentArgs(
                    variables=args["env_vars"]
                ),
                tags=GlobalUtils.get_global_tags(env, {
                    "Name": args["name"],
                }),
                opts=pulumi.ResourceOptions(parent=self, ignore_changes=['environment'])
            )

        if args['trigger']:
            lambda_function.arn.apply(lambda arn: lambda_.EventSourceMapping(
                f"{env}-{args['trigger']}-{args['name']}",
                event_source_arn=args['trigger_arn'],
                function_name=arn,
                batch_size=args['trigger_batch_size'],
                enabled=True,
                opts=pulumi.ResourceOptions(parent=self, ignore_changes=['batchSize','functionResponseTypes','scalingConfig','maximumBatchingWindowInSeconds','functionResponseTypes'])
            ))
