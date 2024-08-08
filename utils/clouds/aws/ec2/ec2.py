from components.clouds.aws.ec2.ec2 import Ec2
from components.clouds.aws.ec2.sg import SG
from utils.shared import GlobalUtils

class Ec2Utils:

    @staticmethod
    def ec2_handler(ec2: Ec2, ec2_dict: dict, env: str, vpc_id: str):
        for server_key in ec2_dict.keys():
            sg_ids = []
            server_dict = ec2_dict[server_key]['ec2_instance']
            for sg_name in server_dict['vpc_security_groups']:
                # Security group created in pulumi so is saved in cache
                if 'security_group' in GlobalUtils.cache_dict and sg_name in GlobalUtils.cache_dict['security_group']:
                    sg_ids.append(GlobalUtils.cache_dict["security_group"][sg_name]['id'])
                # Security group not created by pulumi 
                else:
                    sg_ids.append(SG.get_sg_by_name(sg_name, vpc_id))

            server_dict['vpc_security_groups'] = sg_ids
            ec2.create(env=env, args=server_dict)