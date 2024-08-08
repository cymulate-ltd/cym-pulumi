import pulumi, json, jinja2, os
from pulumi_aws import sqs
from utils.shared import GlobalUtils

class SQS(pulumi.ComponentResource):

    def __init__(self, name, opts = None):
        super().__init__('cymulate:utils:sqs', name, None, opts)
        self.dir_path = os.path.dirname(os.path.abspath(__file__))

        self.name = name

    def create_queue(self, aws_account: str ,region: str, env: str, args: dict):
        
        args["max_message_size"] = args["max_message_size"] if args.get("max_message_size") else 2048
        args["fifo_queue"] = args["fifo_queue"] if args.get("fifo_queue") else False
        args["fifo_throughput_limit"] = args["fifo_throughput_limit"] if args.get("fifo_throughput_limit") else ""
        args["deduplication_scope"] = args["deduplication_scope"] if args.get("deduplication_scope") else ""
        args["content_based_deduplication"] = args["content_based_deduplication"] if args.get("content_based_deduplication") else False
        args["delay_seconds"] = args["delay_seconds"] if args.get("delay_seconds") else 0
        args["message_retention_seconds"] = args["message_retention_seconds"] if args.get("message_retention_seconds") else 86400
        args["receive_wait_time_seconds"] = args["receive_wait_time_seconds"] if args.get("receive_wait_time_seconds") else 0
        args["sqs_managed_sse_enabled"] = args["sqs_managed_sse_enabled"] if args.get("sqs_managed_sse_enabled") else True
        args["visibility_timeout_seconds"] = args["visibility_timeout_seconds"] if args.get("visibility_timeout_seconds") else 0
        args["access_policy"]["source_arn"] = args["access_policy"]["source_arn"] if args["access_policy"].get("source_arn") else ""

        with open(f"{self.dir_path}/../../../templates/clouds/aws/sqs/{args['access_policy']['file_name']}",mode="r") as file:
            policy = jinja2.Template(file.read()).render({"aws_account": aws_account,
                                                            "region": region,
                                                            "queue_name": args["name"],
                                                            "source_arn": args["access_policy"]["source_arn"]})

        # Create a repository
        if args["fifo_queue"] == True:
            queue = sqs.Queue(args["name"],
            name=args["name"],
            delay_seconds=args["delay_seconds"],
            fifo_queue=args["fifo_queue"],
            fifo_throughput_limit=args['fifo_throughput_limit'],
            deduplication_scope=args['deduplication_scope'],
            content_based_deduplication=args['content_based_deduplication'],
            max_message_size=args["max_message_size"],
            message_retention_seconds=args["message_retention_seconds"],
            receive_wait_time_seconds=args["receive_wait_time_seconds"],
            visibility_timeout_seconds=args["visibility_timeout_seconds"],
            sqs_managed_sse_enabled=args["sqs_managed_sse_enabled"],
            policy=policy,
            tags=GlobalUtils.get_global_tags(env, {
            "Name": args['name'],
            }),
            opts=pulumi.ResourceOptions(parent=self)
            )
        else:
            queue = sqs.Queue(args["name"],
                name=args["name"],
                delay_seconds=args["delay_seconds"],
                max_message_size=args["max_message_size"],
                message_retention_seconds=args["message_retention_seconds"],
                receive_wait_time_seconds=args["receive_wait_time_seconds"],
                visibility_timeout_seconds=args["visibility_timeout_seconds"],
                sqs_managed_sse_enabled=args["sqs_managed_sse_enabled"],
                policy=policy,
                tags=GlobalUtils.get_global_tags(env, {
                "Name": args['name'],
                }),
                opts=pulumi.ResourceOptions(parent=self)
            )


        return queue