
import pulumi
from pulumi_aws import rds, ec2
from typing import Sequence
from utils.shared import GlobalUtils

class RDS(pulumi.ComponentResource):

    name: str
    rds_db: pulumi.Output[str]

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:rds', name, None, opts)

        self.name = name

    def create(self, args: dict, security_groups: list):
        args['performance_insights_enabled'] = args['performance_insights_enabled'] if args.get('performance_insights_enabled') else True
        args['performance_insights_retention_period'] = args['performance_insights_retention_period'] if args.get('performance_insights_retention_period') else 7
        args['storage_encrypted'] = args['storage_encrypted'] if args.get('storage_encrypted') else True
        args['ca_cert_identifier'] = args['ca_cert_identifier'] if args.get('ca_cert_identifier') else 'rds-ca-rsa2048-g1'
        args['port'] = args['port'] if args.get('port') else 5432
        args['backup_window'] = args['backup_window'] if args.get('backup_window') else '23:45-00:15'
        args['max_allocated_storage'] = args['max_allocated_storage'] if args.get('max_allocated_storage') else None
        args['enabled_cloudwatch_logs_exports'] = args['enabled_cloudwatch_logs_exports'] if args.get('enabled_cloudwatch_logs_exports') else None

        db_subnet_group_name = self.name + '-subnet-group'

        rds.SubnetGroup(db_subnet_group_name,
            name=db_subnet_group_name,
            subnet_ids=args['subnet_ids'],
            tags=GlobalUtils.get_global_tags(args['env'], { 'Name': db_subnet_group_name }),
            opts=pulumi.ResourceOptions(parent=self,delete_before_replace=True)
        )

        self.rds_db = rds.Instance(identifier=args['name'],
            resource_name=self.name,
            db_name=args['db_name'],
            engine=args['engine'],
            engine_version=args['engine_version'],
            allocated_storage=args['allocated_storage'],
            storage_type="gp3",
            storage_encrypted=args['storage_encrypted'],
            max_allocated_storage=args['max_allocated_storage'] if args['max_allocated_storage'] else 0,
            instance_class=args['instance_class'],
            parameter_group_name=args['parameter_group_name'],
            skip_final_snapshot=True,
            manage_master_user_password=args['manage_master_user_password'] if args['manage_master_user_password'] else False,
            username=args['username'],
            backup_window=args['backup_window'],
            backup_retention_period=args['backup_retention_period'],
            apply_immediately=True,
            publicly_accessible=False,
            vpc_security_group_ids=security_groups,
            multi_az=args['multi_az'],
            ca_cert_identifier=args['ca_cert_identifier'],
            performance_insights_enabled=args['performance_insights_enabled'],
            performance_insights_retention_period=args['performance_insights_retention_period'],
            allow_major_version_upgrade=False,
            auto_minor_version_upgrade=False,
            db_subnet_group_name=db_subnet_group_name,
            enabled_cloudwatch_logs_exports=args['enabled_cloudwatch_logs_exports'],
            tags=GlobalUtils.get_global_tags(args['env'], { 'Name': self.name }),
            opts=pulumi.ResourceOptions(parent=self)
        )

        if args['manage_master_user_password']:
            print('Do not forget to disable rotation at secret manager!')
