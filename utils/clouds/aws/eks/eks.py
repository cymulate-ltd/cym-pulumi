from pulumi_aws import eks
from utils.shared import GlobalUtils

class EKSUtils:

    @staticmethod
    def get_oidc_issuer(eks_name: str):
        # Cache doesn't includes the eks_name
        if eks_name not in GlobalUtils.cache_dict or 'oidc_issuer' not in GlobalUtils.cache_dict[eks_name]:
            eks_cluster = eks.get_cluster(name=eks_name)
            oidc_issuer = eks_cluster.identities[0].oidcs[0].issuer
            # Extracts `{issuer}` from `https://oidc.eks.us-east-1.amazonaws.com/id/{issuer}`
            oidc_issuer = oidc_issuer[oidc_issuer.rfind('/')+1:]
            if not hasattr(GlobalUtils.cache_dict, eks_name):
                GlobalUtils.cache_dict[eks_name] = {}
            GlobalUtils.cache_dict[eks_name]['oidc_issuer'] = oidc_issuer
        return GlobalUtils.cache_dict[eks_name]['oidc_issuer']