config_schema = {
    "type" : "object",
    "properties" : {
        "env" : {"type" : "string"},
        "region" : {"type" : "string"},
        "aws_account" : {"type" : "string"},
        "tenant" : {
            "type" : "object",
            "properties" : {
                "name": {"type": "string"},
                "guid": {"type": "string"},
                "node_env": {"type": "string"},
                "url": {"type": "string"}
            },
            "required":[
                "name", "guid", "node_env"
            ],
            "additionalProperties": False
        },
        "global" : {
            "type" : "object",
            "properties" : {
                "sg": {
                    "type": "array",
                    "required":[
                        "name"
                    ]
                }
            }
        },
        "iam" : {
            "type" : "object",
            "properties" : {
                "roles": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "attach_policies": {"type": "array"},
                                "associated_eks_name": {"type": "string"}
                            },
                            "required": ["name", "attach_policies"]
                        }
                    }
                },
                "policies": {
                    "type": "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "template_path": {"type": "string"},
                                "template_vars": {"type": "object"}
                            },
                            "required": ["name"]
                        }
                    }
                }
            }
        },
        "secret_manager" : {
            "type" : "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "reference_policy": {"type": "string"},
                        "reference_arn": {"type": "string"},
                        "update_json_secret_vars": {"type": "object"},
                    },
                    "required": ["name", "reference_policy", "reference_arn"]
                }
            }
        },
        "security_group" : {
            "type" : "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "associated_sgs": {
                            "type": "array",
                            "properties": {
                                "name": {"type": "string"},
                                "from_port": {"type": "string"},
                                "to_port": {"type": "array"}
                            },
                            "required": ["name", "from_port", "to_port"]
                        },
                        "ingress": {
                            "type": "array",
                            "properties": {
                                "from_port": {"type": "string"},
                                "to_port": {"type": "string"},
                                "cidrs": {"type": "array"},
                                "ipv6_cidr_blocks": {"type": "array"},
                                "description": {"type": "string"}
                            },
                            "required": ["from_port", "to_port"]
                        },
                        "egress": {
                            "type": "array",
                            "properties": {
                                "from_port": {"type": "string"},
                                "to_port": {"type": "string"},
                                "cidrs": {"type": "array"},
                                "ipv6_cidr_blocks": {"type": "array"},
                                "description": {"type": "string"}
                            },
                            "required": ["from_port", "to_port"]
                        },
                    },
                    "required": ["name"]
                }
            }
        },
        "infra" : {
            "type" : "object",
            "properties" : {
                "config": {
                    "type": "object",
                    "vpc": {"type": "array"},
                    "required":[
                        "vpc"
                    ],
                },
                "vpc": {
                    "type": "object",
                    "vpc_id": {"type": "string"},
                    "required":[
                        "vpc_id", "subnets"
                    ],
                    "subnets": {
                        "type": "object",
                        "properties" : {
                            "private": {"type": "array"},
                            "public": {"type": "array"}
                        },
                        "required":[
                            "private", "public"
                        ],
                        "additionalProperties": False
                    },
                    "cidr_blocks": {
                        "type": "array",
                    }
                },
                "cloudfront": {"type": "object"},


                "kubernetes": {
                    "type" : "object",
                    "patternProperties": {
                        ".*": {
                            "type": "object",
                            "properties": {
                                "security_group": {
                                    "patternProperties": {
                                        ".*": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "description": {"type": "string"},
                                                "associated_sgs": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "name": {"type": "string"},
                                                            "description": {"type": "string"},
                                                            "from_port": {"type": "string"},
                                                            "to_port": {"type": "string"},
                                                            "protocol": {"type": ["integer", "string"]},
                                                            "ignore_changes": {"type": "boolean"},
                                                            "extra_tags": {"type": "object"}
                                                        },
                                                        "required": ["name", "description", "from_port", "to_port"]
                                                    }
                                                },
                                                "egress": {
                                                    "type": "array",
                                                    "items": {
                                                        "type": "object",
                                                        "properties": {
                                                            "from_port": {"type": "string"},
                                                            "to_port": {"type": "string"},
                                                            "protocol": {"type": "string"},
                                                            "cidrs": {
                                                                "type": "array",
                                                                "items": {"type": "string"}
                                                            },
                                                            "description": {"type": "string"},
                                                        },
                                                        "required": ["from_port", "to_port", "protocol", "cidrs", "description"]
                                                    }
                                                }
                                            },
                                            "required": ["name", "description"]
                                        }
                                    }
                                },
                                "cluster": {
                                    "type": "object",
                                    "properties": {
                                        "cluster_name": {"type": "string"},
                                        "version": {"type": "string"},
                                        "eks_cluster_log_types": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        },
                                        "vpc_config": {
                                            "type": "object",
                                            "properties": {
                                                "subnet_ids": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                },
                                                "public_access_cidrs": {
                                                    "type": "array",
                                                    "items": {"type": "string"}
                                                }
                                            },
                                            "required": ["subnet_ids", "public_access_cidrs"]
                                        }
                                    },
                                    "required": ["cluster_name", "version", "eks_cluster_log_types", "vpc_config"]
                                },
                                "node_groups": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "node_group_type": {"type": "string"},
                                            "name": {"type": "string"},
                                            "subnet_ids": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            },
                                            "eks_node_group": {"type": "string"},
                                            "capacity_type": {"type": "string"},
                                            "scaling_config": {
                                                "type": "object",
                                                "properties": {
                                                    "desired_size": {"type": "integer"},
                                                    "min_size": {"type": "integer"},
                                                    "max_size": {"type": "integer"}
                                                },
                                                "required": ["desired_size", "min_size", "max_size"]
                                            },
                                            "taint": {"type": "string"},
                                            "launch_template": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "ami_id": {"type": "string"},
                                                    "instance_type": {"type": "string"},
                                                    "key_name": {"type": "string"},
                                                    "public_ip": {"type": "boolean"},
                                                    "block_device_mappings": {
                                                        "type": "object",
                                                        "properties": {
                                                            "device_name": {"type": "string"},
                                                            "ebs": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "encrypted": {"type": "string"},
                                                                    "volume_size": {"type": "integer"},
                                                                    "volume_type": {"type": "string"}
                                                                },
                                                                "required": ["encrypted", "volume_size", "volume_type"]
                                                            }
                                                        },
                                                        "required": ["device_name", "ebs"]
                                                    },
                                                    "network_interfaces": {
                                                        "type": "object",
                                                        "properties": {
                                                            "public_ip": {"type": "boolean"}
                                                        },
                                                        "required": ["public_ip"]
                                                    },
                                                    "metadata_options": {
                                                        "type": "object",
                                                        "properties": {
                                                            "http_endpoint": {"type": "string"},
                                                            "http_tokens": {"type": "string"}
                                                        },
                                                        "required": ["http_endpoint", "http_tokens"]
                                                    }
                                                },
                                                "required": ["name", "ami_id", "instance_type", "key_name", "public_ip", "block_device_mappings", "network_interfaces"]
                                            },
                                            "autoscaling": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string"},
                                                    "desired_capacity": {"type": "integer"},
                                                    "min_size": {"type": "integer"},
                                                    "max_size": {"type": "integer"},
                                                    "vpc_zone_identifier": {
                                                        "type": "array",
                                                        "items": {"type": "string"}
                                                    },
                                                    "mixed_instances_policy": {
                                                        "type": "object",
                                                        "properties": {
                                                            "launch_template": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "overrides": {
                                                                        "type": "array",
                                                                        "items": {}
                                                                    }
                                                                },
                                                                "required": ["overrides"]
                                                            },
                                                            "instances_distribution": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "ec2_on_demand_base_capacity": {"type": "integer"},
                                                                    "ec2_on_demand_percentage_above_base_capacity": {"type": "integer"}
                                                                },
                                                                "required": ["ec2_on_demand_base_capacity", "ec2_on_demand_percentage_above_base_capacity"]
                                                            }
                                                        },
                                                        "required": ["launch_template", "instances_distribution"]
                                                    }
                                                },
                                                "required": ["name", "desired_capacity", "min_size", "max_size", "vpc_zone_identifier", "mixed_instances_policy"]
                                            }
                                        },
                                        "required": ["node_group_type", "name", "subnet_ids", "eks_node_group", "capacity_type", "scaling_config", "taint", "launch_template"]
                                    }
                                }
                            },
                            "required": ["security_group", "cluster", "node_groups"]
                        }
                    }
                },

                
                "ebs": {
                    "type" : "object",
                    "properties" : {
                        "default_encryption": {
                            "type": "object",
                            "properties" : {
                                "enable": {"type": "boolean"},
                                "kms_key": {"type": "string"}
                            },
                            "required": ["enable", "kms_key"]
                        }
                    }
                },
                "codeartifact": {
                    "type" : "object",
                    "properties" : {
                        "repositories": {
                            "type": "array",
                            "properties" : {
                                "repo_name": {"type": "string"},
                                "description": {"type": "string"},
                                "domain": {"type": "string"}
                            },
                            "required": ["enable", "kms_key"]
                        }
                    }
                },
                "cloudtrail": {
                    "type" : "object",
                    "properties" : {
                        "default_encryption": {
                            "type": "object",
                            "properties" : {
                                "enable": {"type": "boolean"},
                                "kms_key": {"type": "string"}
                            },
                            "required": ["enable", "kms_key"]
                        }
                    }
                },
            },
            "additionalProperties": False
        },
        "db" : {
            "type" : "object",
            "properties" : {
                "rds": {"type": "array"},
                "atlas": {"type": "object"},
                "msk": { "type": "array",
                    "properties": {
                        ".*": {"type": "string"},
                        "kafka_version": {"type": "string"},
                        "number_of_broker_nodes": {"type": "integer"},
                        "instance_type": {"type": "string"},
                        "env": {"type": "string"},
                        "client_subnets": {
                            "type": "array",
                            "items": {"type": "string"}
                            },
                        "volume_size": {"type": "integer"},
                        "kms_arn": {"type": "string"},
                        },
                    "required": ["name", "kafka_version", "number_of_broker_nodes", "instance_type", "env", "client_subnets", "volume_size"]
                }
            },
        },
        "queue": {
            "type" : "object",
            "properties" : {
                "sqs": {"type": "array"},
            }
        },
        "eventbridge": {
        "type": "object",
        "properties": {
            "event_rules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                "name": {
                    "type": "string"
                },
                "file_name": {
                    "type": "string"
                }
                },
                "required": ["name", "file_name"]
            }
            },
            "event_rule_targets": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                "event_target_arn": {
                    "type": "string"
                },
                "rule_name": {
                    "type": "string"
                }
                },
                "required": ["event_target_arn", "rule_name"]
            }
            }
        }
        },
        "lambda": {
            "type" : "object",
            "properties" : {
                "function": {
                    "type": "array",
                    "properties" : {
                        "name": {"type": "string"},
                        "role_name": {"type": "string"},
                        "image_uri": {"type": "string"},
                        "attached_security_groups_names": {"type": "array"},
                        "vpc_config": {"type": "array",
                        "properties": { 
                                "vpc_id": {"type": "string"},
                                "subnets_ids": {"type": "array",
                                    "properties": {"subnets_id": {"type": "string"}
                                },
                            },
                            }
                        },
                        "env_vars": {"type": "object"}
                    },
                }
            }
        },
        "servers" : {
            "type" : "object",
            "properties" : {
                "dlp": {"type": "array"},
                "fileserver": {"type": "array"}
            },
            "required":[],
            "additionalProperties": True
        },
    },
    "additionalProperties": False
}