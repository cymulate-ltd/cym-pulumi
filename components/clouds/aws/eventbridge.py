import pulumi, json, jinja2, os
from pulumi_aws import cloudwatch
from utils.shared import GlobalUtils

class EventBridge(pulumi.ComponentResource):

    def __init__(self, name, opts = None):
        super().__init__('cymulate:utils:eventbridge', name, None, opts)
        self.dir_path = os.path.dirname(os.path.abspath(__file__))

        self.name = name
        
    def create_cloudwatch_event_rule(self, region: str, args: dict):
        with open(f"{self.dir_path}/../../../templates/clouds/aws/eventbridge/{args['file_name']}",mode="r") as file:
            event_pattern = jinja2.Template(file.read()).render()


        rule = cloudwatch.EventRule(args["name"],
                                    name=args["name"],
                                    event_pattern=event_pattern,
                                    tags=GlobalUtils.get_global_tags(region, {
                                        "Name": args['name'],
                                    }),
                                    opts=pulumi.ResourceOptions(parent=self)
                                )
        return rule
        
    def create_cloudwatch_event_target(self, args: dict):
        target_event = cloudwatch.EventTarget(args["rule_name"],
                                            rule=args["rule_name"],
                                            arn=args["event_target_arn"], 
                                            opts=pulumi.ResourceOptions(parent=self))
        
        return target_event