from typing import Literal
import pulumi
from pulumi_aws import ec2
from components.clouds.aws.ec2.sg import SG
from utils.shared import GlobalUtils

class SGUtils:

    @staticmethod
    def sg_handler(sg: SG, sg_dict: dict, env: str, vpc_id: str):
        GlobalUtils.cache_dict["security_group"] = {}

        # Some security groups cannot attach rules with conflicts for example: sg that set the same sg as ingress rule (the sg hasn't been created yet)
        # Or two sgs that set rules of the other sg, we can't know which one to create first
        # This code section seperate those rules and create only the rules association after the sgs created without them
        for sg_key in sg_dict.keys():
            sg_value = sg_dict[sg_key]

            if 'associated_sgs' in sg_value:
                for ref_sg in sg_value['associated_sgs']:
                    # The associated security group has the same name as the parent security group
                    if ref_sg['name'] == sg_value['name']:
                        sg_value['sg_rules_seperated'] = True
                        break

                    # Looking for the associated sg from the dict
                    if ref_sg['name'] in sg_dict:
                        tmp_sg_value = sg_dict[ref_sg['name']]
                        if 'associated_sgs' in tmp_sg_value:
                            for tmp_ref_sg in tmp_sg_value['associated_sgs']:
                                # Looping over the associated sg `associated_sgs`
                                # if the associated sg `associated_sgs` has same sg name as the original sg we started from
                                # Remove from the associated_sgs list and process later as sg rule alone after the sg created
                                if tmp_ref_sg['name'] == sg_value['name']:
                                    sg_value['sg_rules_seperated'] = True
                                    break
                                    
            if 'ingress' in sg_value and 'associated_sgs' in sg_value:
                sg_value['sg_ingress_rule_seperated'] = True

        # Loop to add the security groups without sg rules first
        for sg_key in sg_dict.keys():
            sg_value = sg_dict[sg_key]
            
            # Install no-depended security groups
            if 'associated_sgs' not in sg_value:
                ingress_rules = SGUtils.get_security_group_rules(sg=sg, type='ingress', sg_dict=sg_value['ingress'])
                egress_rules = SGUtils.get_security_group_rules(sg=sg, type='egress', sg_dict=sg_value['egress'])
                
                # Creates security group
                _sg = sg.create(
                    env=env,
                    name=sg_value['name'],
                    vpc_id=vpc_id,
                    description=sg_value.get('description', ''),
                    ingress_rules=ingress_rules,
                    egress_rules=egress_rules,
                    ignore_changes=sg_value.get('ignore_changes', False),
                    extra_tags=sg_value.get('extra_tags', {})
                )
                GlobalUtils.cache_dict["security_group"][sg_value['name']] = { 'id': _sg.id }
        
        for sg_key in sg_dict.keys():
            sg_value = sg_dict[sg_key]

            # Install only depended security groups
            if 'associated_sgs' in sg_value:
                ingress_rules = []
                
                try:
                    egress_rules = SGUtils.get_security_group_rules(sg=sg, type='egress', sg_dict=sg_value['egress'])
                except Exception as e:
                    egress_rules = []

                # Loop over list of security groups to reference current sg
                if 'sg_rules_seperated' not in sg_value and 'sg_ingress_rule_seperated' not in sg_value:
                    for ref_sg in sg_value['associated_sgs']:
                        if ref_sg['name'] not in GlobalUtils.cache_dict["security_group"]:
                            reference_sg_id = SG.get_sg_by_name(name=ref_sg['name'], vpc_id=vpc_id)
                            ref_sg['security_group_ids'] = [reference_sg_id]
                        else:
                            ref_sg['security_group_ids'] = [GlobalUtils.cache_dict["security_group"][ref_sg['name']]['id']]
                        ingress_rules += SGUtils.get_security_group_rules(sg=sg, type='ingress', sg_dict=[ref_sg])

                # Creates security group
                sg_params = {}
                if len(ingress_rules) > 0:
                    sg_params['ingress'] = ingress_rules
                if len(egress_rules) > 0:
                    sg_params['egress'] = egress_rules
                
                ignore_changes_list = []
                if 'ignore_changes' in sg_value:
                    ignore_changes_list = ['ingress', 'egress']

                _sg = ec2.SecurityGroup(sg_value['name'],
                    name=sg_value['name'],
                    description=sg_value.get('description', None),
                    vpc_id=vpc_id,
                    **sg_params,
                    tags=GlobalUtils.get_global_tags(env, { 'Name': sg_value['name'], **sg_value.get('extra_tags', {}) }),
                    opts=pulumi.ResourceOptions(parent=sg, ignore_changes=ignore_changes_list)
                )
                
                GlobalUtils.cache_dict["security_group"][sg_value['name']] = { 'id': _sg.id }
        
        for sg_key in sg_dict.keys():
            sg_value = sg_dict[sg_key]
            
            if 'sg_rules_seperated' in sg_value:
                for index, ref_sg in enumerate(sg_value['associated_sgs']):
                    ec2.SecurityGroupRule(
                        f"{sg_value['name']}-{ref_sg['name']}-{index}",
                        type='ingress',
                        description=ref_sg.get('description', ''),
                        from_port=ref_sg['from_port'],
                        to_port=ref_sg['to_port'],
                        protocol=ref_sg.get('protocol', 'tcp'),
                        security_group_id=GlobalUtils.cache_dict["security_group"][sg_value['name']]['id'],
                        source_security_group_id=GlobalUtils.cache_dict["security_group"][ref_sg['name']]['id'],
                        opts=pulumi.ResourceOptions(parent=sg)
                    )
            elif 'sg_ingress_rule_seperated' in sg_value:
                for index, sg_rule in enumerate(sg_value['ingress']):
                    ec2.SecurityGroupRule(
                        f"{sg_value['name']}-{index}",
                        type='ingress',
                        description=sg_rule.get('description', ''),
                        from_port=sg_rule['from_port'],
                        to_port=sg_rule['to_port'],
                        protocol=sg_rule.get('protocol', 'tcp'),
                        security_group_id=GlobalUtils.cache_dict["security_group"][sg_value['name']]['id'],
                        cidr_blocks=sg_rule['cidrs'],
                        opts=pulumi.ResourceOptions(parent=sg)
                    )

    @staticmethod
    def get_security_group_rules(sg: SG, type: Literal['ingress', 'egress'], sg_dict: dict) -> list:
        sg_rules = []
        for sg_rule in sg_dict:
            from_ports = sg_rule['from_port'].split(',')
            to_ports = sg_rule['to_port'].split(',')

            if len(from_ports) != len(to_ports):
                raise Exception('from_ports array length is differ from to_ports array length!')

            for i in range(len(from_ports)):
                sg_rules.append(sg.get_sg_rule(
                    type=type,
                    description=sg_rule.get('description', ''),
                    from_port=from_ports[i],
                    to_port=to_ports[i],
                    protocol=sg_rule.get('protocol', 'tcp'),
                    security_group_ids=sg_rule.get('security_group_ids', None),
                    cidr_blocks=sg_rule.get('cidrs', None),
                    ipv6_cidr_blocks=sg_rule.get('ipv6_cidr_blocks', None)
                ))
        return sg_rules