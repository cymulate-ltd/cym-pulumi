import pulumi, json
import pulumi_random as random
from pulumi_aws import msk
from utils.shared import GlobalUtils
from components.clouds.aws.kms import KMS
from components.clouds.aws.secret_manager import SecretManager


class MSK(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts=None):
        super().__init__("cymulate:utils:msk", name, None, opts)

    def create(self, args: dict, security_groups):
        kms = KMS(name="msk", opts=pulumi.ResourceOptions(parent=self))
        secret_manager = SecretManager(name="secret", opts=pulumi.ResourceOptions(parent=self))
        
        args["create_secret_in_region"] = args.get("create_secret_in_region", False)

        # Create MSK Cluster config
        kafka_version_str = args["kafka_version"]
        kafka_version_list = [kafka_version_str]
        msk_config = msk.Configuration(
            resource_name=f"{args['env']}-kafka-config",
            kafka_versions=kafka_version_list,
            server_properties=(
                f"auto.create.topics.enable=true\n"
                f"default.replication.factor={args['number_of_broker_nodes']}\n"
                f"min.insync.replicas={args['number_of_broker_nodes'] - 1}\n"
                f"num.io.threads=8\n"
                f"num.network.threads=5\n"
                f"num.partitions=1\n"
                f"num.replica.fetchers=2\n"
                f"replica.lag.time.max.ms=30000\n"
                f"socket.receive.buffer.bytes=102400\n"
                f"socket.request.max.bytes=104857600\n"
                f"socket.send.buffer.bytes=102400\n"
                f"unclean.leader.election.enable=true\n"
                f"zookeeper.session.timeout.ms=18000\n"
                f"group.initial.rebalance.delay.ms=180000\n"
                f"allow.everyone.if.no.acl.found=true\n"
                f"transaction.state.log.replication.factor={args['number_of_broker_nodes']}\n"
                f"offsets.topic.replication.factor={args['number_of_broker_nodes']}\n"
            ),
            name=f"{args['env']}-kafka-config",
            opts=pulumi.ResourceOptions(parent=self),
        )


        # Create secret to hold Username and Password
        auth_token = random.RandomPassword(args['name'],
            length=16,
            special=True,
            lower=True,
            numeric=True,
            upper=True,
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        custom_key = kms.create_kms_key(f"{args['env']}-kafka", 
                                        description="Custom KMS Key for MSK Cluster Scram Secret Association",
                                        tags=GlobalUtils.get_global_tags(args["env"], {"Name": args["name"]}),
                                        )

        secret_arn = secret_manager.create_json_secret_from_output(
            name=f"AmazonMSK_{args['env']}-kafka",
            output_json_str= auth_token.result.apply(self.get_msk_json),
            kms_key_id=custom_key.id,
            create_secret_in_region=args['create_secret_in_region'],
            tags=GlobalUtils.get_global_tags(args["env"], {"Name": args["name"]})
        )

        # Create MSK Cluster
        msk_inst = msk.Cluster(
            resource_name=args["name"],
            cluster_name=args["name"],
            configuration_info=msk.ClusterConfigurationInfoArgs(
                arn=msk_config.arn, revision=msk_config.latest_revision
            ),
            kafka_version=args["kafka_version"],
            number_of_broker_nodes=args["number_of_broker_nodes"],
            broker_node_group_info=msk.ClusterBrokerNodeGroupInfoArgs(
                client_subnets=args["client_subnets"],
                instance_type=args["instance_type"],
                security_groups=security_groups,
                storage_info=msk.ClusterBrokerNodeGroupInfoStorageInfoArgs(
                    ebs_storage_info=msk.ClusterBrokerNodeGroupInfoStorageInfoEbsStorageInfoArgs(
                        volume_size=args["volume_size"]
                    )
                ),
            ),
            encryption_info=msk.ClusterEncryptionInfoArgs(
                encryption_at_rest_kms_key_arn=(
                    args["kms_arn"]
                    if args.get("kms_arn")
                    else kms.create_kms_key(args["name"]).arn
                )
            ),
            client_authentication={
                "sasl": {
                    "iam": True,
                    "scram": True,
                },
                "unauthenticated": False,
            },
            logging_info={
                "brokerLogs": {
                    "cloudwatchLogs": {
                        "enabled": True,
                        "logGroup": args["name"],
                    },
                    "firehose": {
                        "enabled": False,
                        "deliveryStream": "",
                    },
                    "s3": {
                        "enabled": False,
                        "bucket": "",
                        "prefix": "",
                    },
                },
            },
            tags=GlobalUtils.get_global_tags(args["env"], {"Name": args["name"]}),
            opts=pulumi.ResourceOptions(parent=self),
        )

        # Create scram_secret_association
        scram_secret_association = msk.ScramSecretAssociation(f"{args['env']}-kafka",
            cluster_arn=msk_inst.arn,
            secret_arn_lists=[secret_arn],
            opts = pulumi.ResourceOptions(parent=self))

        return msk_inst

    def get_msk_json(self, password):
        return json.dumps(
            {"username": "cym-msk", "password": password}
        )
