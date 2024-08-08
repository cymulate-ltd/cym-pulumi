import pulumi
import pulumi_tls as tls
from pulumi_aws import eks
from pulumi_aws.iam import Role
from utils.shared import GlobalUtils
from components.clouds.aws.iam import IAM
from components.clouds.aws.ec2.sg import SG
from components.clouds.aws.eks.node_group import NodeGroup

class EKS(pulumi.ComponentResource):

    name: str

    def __init__(self, name: str, opts = None):
        super().__init__('cymulate:utils:eks', name, None, opts)
        self.name = name

    def create(self, env: str, args: dict):
        iam = IAM(self.name, opts=pulumi.ResourceOptions(parent=self))
        ng = NodeGroup(self.name, opts=pulumi.ResourceOptions(parent=self))

        cluster_iam_role: Role = iam.create_role(
            role_name=f"eks-cluster-role-{env}",
            policy_names=["AmazonEKSClusterPolicy", "AmazonEKSServicePolicy", "CloudWatchAgentServerPolicy"],
            policy_arns=["arn:aws:iam::aws:policy/AmazonEKSClusterPolicy", "arn:aws:iam::aws:policy/AmazonEKSServicePolicy", "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"],
            template_path="templates/clouds/aws/eks/iam/policies/eks_assume_role_policy.j2"
        )
        
        cluster_args = args['cluster']
        cluster_args['vpc_config']['endpoint_private_access'] = cluster_args['vpc_config'].get('endpoint_private_access', True)
        cluster_args['vpc_config']['endpoint_public_access'] = cluster_args['vpc_config'].get('endpoint_public_access', True)

        _eks = eks.Cluster(cluster_args['cluster_name'],
            name=cluster_args['cluster_name'],
            role_arn=cluster_iam_role.arn,
            version=cluster_args["version"],
            enabled_cluster_log_types=cluster_args['eks_cluster_log_types'],

            vpc_config=eks.ClusterVpcConfigArgs(
                security_group_ids=[GlobalUtils.cache_dict['security_group'][f'eks-cluster-{env}']['id']],
                subnet_ids=cluster_args['vpc_config']['subnet_ids'],
                endpoint_private_access=cluster_args['vpc_config']['endpoint_private_access'],
                endpoint_public_access=cluster_args['vpc_config']['endpoint_public_access'],
                public_access_cidrs=cluster_args['vpc_config']['public_access_cidrs']
            ),

            tags=GlobalUtils.get_global_tags(env, { "Name": self.name }),
            opts=pulumi.ResourceOptions(parent=self)
        )
        
        # Enabling IAM Roles for Service Accounts

        cert_issuer = _eks.identities.apply(lambda identities: tls.get_certificate_output(url=identities[0].oidcs[0].issuer))

        iam.create_iam_openid_connect_provider(
            name=self.name,
            client_id_lists=["sts.amazonaws.com"],
            thumbprint_lists=[cert_issuer.certificates[0].sha1_fingerprint],
            url=cert_issuer.url
        )

        # Create Node Groups resources

        cloudwatch_logs_ship_policy = iam.create_policy(
            policy_name=f"eks-cloudwatch-logs-ship-{env}",
            description="allow eks worker nodes to ship logs to cloudwatch",
            template_path="templates/clouds/aws/eks/iam/policies/cloudwatch_logs_ship.j2"
        )

        eks_assume_policy = iam.create_policy(
            policy_name=f"eks-assume-role-{env}",
            description="allow eks worker nodes to assume roles that will be allowed by the destination IAM role",
            template_path="templates/clouds/aws/eks/iam/policies/eks_assume_policy.j2"
        )

        worker_iam_role: Role = iam.create_role(
            role_name=f"eks-worker-node-role-{env}",
            policy_names=[f"eks-cloudwatch-logs-ship-{env}", f"eks-assume-role-{env}", "AmazonEKSWorkerNodePolicy", "AmazonEKS_CNI_Policy", "AmazonEC2ContainerRegistryReadOnly"],
            policy_arns=[cloudwatch_logs_ship_policy.arn, eks_assume_policy.arn, "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy", "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy", "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"],
            template_path="templates/clouds/aws/eks/iam/policies/ec2_assume_role_policy.j2"
        )

        eks_instance_profile = iam.create_instance_profile(
            name=f"eks-inst-profile-{env}",
            role_name=worker_iam_role.name
        )

        for node_group_args in args['node_groups']:
            node_group_args['launch_template']['user_data'] = {}
            node_group_args['launch_template']['user_data']['eks_endpoint'] = _eks.endpoint
            node_group_args['launch_template']['user_data']['eks_cluster_ca'] = _eks.certificate_authorities[0].data
            ng.create(env=env, cluster_name=cluster_args['cluster_name'], node_role_arn=worker_iam_role.arn, instance_profile_arn=eks_instance_profile.arn, args=node_group_args)

        return _eks.arn