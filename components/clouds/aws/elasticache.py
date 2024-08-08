import pulumi
import pulumi_random as random
from pulumi_aws import elasticache
from utils.shared import GlobalUtils

class ElastiCache(pulumi.ComponentResource):


    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:elasticache', name, None, opts)

    def create(self, args: dict):
        auth_token = random.RandomPassword(args['name'],
            length=16,
            special=True,
            lower=True,
            numeric=True,
            upper=True,
            opts=pulumi.ResourceOptions(parent=self)
        )

        args['port'] = args['port'] if args.get('port') else 6379
        args['apply_immediately'] = args['apply_immediately'] if args.get('apply_immediately') else True
        args['at_rest_encryption_enabled'] = args['at_rest_encryption_enabled'] if args.get('at_rest_encryption_enabled') else True
        args['transit_encryption_enabled'] = args['transit_encryption_enabled'] if args.get('transit_encryption_enabled') else True
        args['auto_minor_version_upgrade'] = args['auto_minor_version_upgrade'] if args.get('auto_minor_version_upgrade') else False
        args['multi_az_enabled'] = args['multi_az_enabled'] if args.get('multi_az_enabled') else False
        args['network_type'] = args['network_type'] if args.get('network_type') else "ipv4"
        
        elasticache_subnet_name = elasticache.SubnetGroup(resource_name=args['subnet_group_name'],
            name=args['subnet_group_name'],
            description=f"Elasticache subnet group for {args['name']} replication group",
            subnet_ids=args['subnets'],
            tags=GlobalUtils.get_global_tags(args['env'], { 'Name': args["name"]}),
            opts=pulumi.ResourceOptions(parent=self, ignore_changes=["authToken"])
        )

        elasticache_inst = elasticache.ReplicationGroup(resource_name=args['name'],
            apply_immediately=args['apply_immediately'],
            at_rest_encryption_enabled=args['at_rest_encryption_enabled'],
            auth_token=auth_token.result,
            auto_minor_version_upgrade=args['auto_minor_version_upgrade'],
            description=f"Elasticache replication group for {args['env']} environment",
            engine_version=args['engine_version'],
            maintenance_window=args['maintenance_window'],
            multi_az_enabled=args['multi_az_enabled'],
            network_type=args['network_type'],
            node_type=args['node_type'],
            num_cache_clusters=args['num_cache_clusters'],
            parameter_group_name=args['parameter_group_name'],
            port=args['port'],
            subnet_group_name=elasticache_subnet_name.name,
            transit_encryption_enabled=args['at_rest_encryption_enabled'],
            tags=GlobalUtils.get_global_tags(args['env'], { 'Name': args["name"] }),
            opts=pulumi.ResourceOptions(parent=self, ignore_changes=["authToken"])
        )
        
        redis_password = auth_token.result.apply(lambda v: f"{v}")
        pulumi.export(f"{args['name']}-password", redis_password)
        
        return elasticache_inst
