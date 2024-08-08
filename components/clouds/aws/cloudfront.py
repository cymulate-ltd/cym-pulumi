import pulumi, json, boto3
import pulumi_tls as tls
from pulumi_aws import cloudfront
from utils.shared import GlobalUtils
from components.clouds.aws.secret_manager import SecretManager 

class CloudFront(pulumi.ComponentResource):

    distribution_id: pulumi.Output[str]

    def __init__(self,
        name: str,
        opts=None
    ):
        super().__init__('cymulate:utils:cloudfront', name, None, opts)

    def get_cloudfront_distribution_by_comment(self, comment: str):
        cloudfront_client = boto3.client('cloudfront')
        distributions = cloudfront_client.list_distributions()

        for distribution in distributions['DistributionList']['Items']:
            distribution_env = distribution['Comment']

            if distribution_env == comment:
                return distribution

        return None

    
    def create(self, args: dict, opts = None):
        exist_distribution = self.get_cloudfront_distribution_by_comment(comment=args["env"])
        # Create CloudFront origin access control
        cf_origin_access_control = None
        if len(args['s3_origins']) > 0:
            cf_origin_access_control = cloudfront.OriginAccessControl(
                f'{args["env"]}-{args["s3_origins"][0]["origin_id"]}'[:64],
                name = f'{args["env"]}-{args["s3_origins"][0]["origin_id"]}'[:64],
                description = args['s3_origins'][0]['origin_id'],
                origin_access_control_origin_type = "s3",
                signing_behavior = "always",
                signing_protocol = "sigv4",
                opts=pulumi.ResourceOptions(parent=self)
            )
        
        should_create_pb = True if args['default_cache_methods'].get('restrict_viewer_access') else False
        if not should_create_pb:
            should_create_pb = any('restrict_viewer_access' in d for d in args['ordered_cache_behaviors'])
        if should_create_pb:
            private_key_secret_name = f'cloudfront-{args["env"]}-private-key'
            secret_manager = SecretManager(private_key_secret_name)
            private_key = tls.PrivateKey(private_key_secret_name,
                algorithm="RSA",
                ecdsa_curve="P224",
                rsa_bits=2048,
                opts=pulumi.ResourceOptions(parent=self)
            )
            
            secret_manager.create_json_secret_from_output(name=private_key_secret_name,
                                              output_json_str=private_key.private_key_pem.apply(self.get_private_key_json)
                                            )

            public_key = cloudfront.PublicKey(f'{args["env"]}-pb-key',
                name=f'{args["env"]}-pb-key',
                comment=f'{args["env"]}-pb-key',
                encoded_key=private_key.public_key_pem,
                opts=pulumi.ResourceOptions(parent=self, ignore_changes=['encoded_key'])
            )

            trusted_key_group = cloudfront.KeyGroup(
                f'{args["env"]}-key-group',
                name=f'{args["env"]}-key-group',
                items=[public_key.id],
                opts=pulumi.ResourceOptions(parent=self, depends_on=[public_key])
            )
            
        # Create CloudFront origins for the distribution
        cf_origins = []
        for s3_origin in args["s3_origins"]:
            if s3_origin['origin_path'] and exist_distribution:
                for index, item in enumerate(exist_distribution['Origins']['Items']):
                  if exist_distribution['Origins']['Items'][index]['Id'] == s3_origin['origin_id']:
                    s3_origin['origin_path'] = exist_distribution['Origins']['Items'][index]['OriginPath']
                    break
            
            cf_origin = cloudfront.DistributionOriginArgs(
                origin_id=s3_origin['origin_id'],
                domain_name=s3_origin['domain_name'],
                origin_path=s3_origin['origin_path'],
                origin_access_control_id=cf_origin_access_control.id
            )
            cf_origins.append(cf_origin)

        # Create CloudFront custom origins for the distribution
        cf_custom_origins = []
        for custom_origin in args['custom_origins']:
            cf_custom_origin = cloudfront.DistributionOriginArgs(
                origin_id=custom_origin['origin_id'],
                domain_name=custom_origin['domain_name'],
                origin_path=custom_origin['origin_path'],
                custom_origin_config=cloudfront.DistributionOriginCustomOriginConfigArgs(
                    http_port="80",
                    https_port="443",
                    origin_protocol_policy="https-only",
                    origin_ssl_protocols=["TLSv1.2"],
                    origin_read_timeout=custom_origin["origin_read_timeout"]
                )
            )
            cf_custom_origins.append(cf_custom_origin)

        # Create CloudFront default cache behavior
        default_cache_behavior = cloudfront.DistributionDefaultCacheBehaviorArgs(
            allowed_methods=args['default_cache_methods']['allowed_methods'],
            cached_methods=args['default_cache_methods']['cached_methods'],
            target_origin_id=args['default_cache_methods']['target_origin_id'],
            cache_policy_id=args['default_cache_methods']['cache_policy_id'],
            origin_request_policy_id=args['default_cache_methods']['origin_request_policy_id'],
            response_headers_policy_id=args['default_cache_methods']['response_headers_policy_id'],
            
            min_ttl=args['default_cache_methods'].get('min_ttl', 0),
            default_ttl=args['default_cache_methods'].get('default_ttl', 0),
            max_ttl=args['default_cache_methods'].get('max_ttl', 0),
            compress=args['default_cache_methods']['compress'],
            viewer_protocol_policy = args['default_cache_methods']['viewer_protocol_policy'],

            function_associations=[cloudfront.DistributionDefaultCacheBehaviorFunctionAssociationArgs(
                event_type='viewer-response',
                function_arn=args['default_cache_methods']['function_association_arn']
            )]
        )
        if args['default_cache_methods'].get('restrict_viewer_access'):
            default_cache_behavior.trusted_key_groups=[trusted_key_group.id]

        cf_ordered_cache_behaviors = []
        for behavior in args['ordered_cache_behaviors']:
            cf_ordered_behavior = cloudfront.DistributionOrderedCacheBehaviorArgs(
                path_pattern=behavior['path_pattern'],
                allowed_methods=behavior['allowed_methods'],
                cached_methods=behavior['cached_methods'],
                target_origin_id=behavior['target_origin_id'],
                cache_policy_id=behavior['cache_policy_id'],
                origin_request_policy_id=behavior['origin_request_policy_id'],
                response_headers_policy_id=behavior['response_headers_policy_id'],
                min_ttl=behavior.get('min_ttl', 0),
                default_ttl=behavior.get('default_ttl', 0),
                max_ttl=behavior.get('max_ttl', 0),
                compress=behavior['compress'],
                viewer_protocol_policy=behavior['viewer_protocol_policy']
            )
            if behavior.get('restrict_viewer_access'):
                cf_ordered_behavior.trusted_key_groups=[trusted_key_group.id]
            cf_ordered_cache_behaviors.append(cf_ordered_behavior)

        # Create CloudFront custom error responses
        cf_custom_error_responses = []
        for error_response in args['custom_error_responses']:
            cf_error_response = cloudfront.DistributionCustomErrorResponseArgs(
                error_code=error_response['error_code'],
                response_code=error_response['response_code'],
                error_caching_min_ttl=error_response.get('error_caching_min_ttl', 10),
                response_page_path=error_response['response_page_path'],
            )
            cf_custom_error_responses.append(cf_error_response)

        # Create CloudFront distribution
        distribution = cloudfront.Distribution(
            args['env'],
            enabled=True,
            is_ipv6_enabled=True,
            comment=args['env'],
            default_root_object=args['default_root_object'],
            price_class=args['price_class'],
            aliases=args['alternate_domain_names'],
            web_acl_id="arn:aws:wafv2:us-east-1:<account-number>:global/webacl/cloudflare-ips-acl/4ab54be7-9808-437a-8955-1460b7d124af",
            origins=cf_origins + cf_custom_origins,
            default_cache_behavior=default_cache_behavior,
            ordered_cache_behaviors=cf_ordered_cache_behaviors,
            custom_error_responses=cf_custom_error_responses,
            restrictions=cloudfront.DistributionRestrictionsArgs(
                geo_restriction=cloudfront.DistributionRestrictionsGeoRestrictionArgs(restriction_type="none")
            ),
            viewer_certificate=cloudfront.DistributionViewerCertificateArgs(
                cloudfront_default_certificate=False,
                acm_certificate_arn=args['acm_certificate_arn'],
                minimum_protocol_version="TLSv1.2_2021",
                ssl_support_method="sni-only"
            ),
            tags=GlobalUtils.get_global_tags(args['env'], { 'MainTenant': args['main_tenant'] }),
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.distribution_id = distribution.id

    def get_private_key_json(self, key):
        return json.dumps({
            "private_key": key
        })