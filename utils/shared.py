import yaml, os
from jsonschema import validate
from schemas.config_schema import config_schema

class GlobalUtils:

    # Load the merged config to this global variable to be accessed from everywhere
    config_dict: dict = {}
    # Used to store reaccuring objects
    cache_dict: dict = {}

    @staticmethod
    def get_global_tags(env: str, extra_tags: dict):
        global_tags = {
            'Environment': env,
            'Pulumi': 'True'
        }
        
        return dict(list(global_tags.items()) + list(extra_tags.items()))

    @staticmethod
    def get_all_config_paths(dir_path: str) -> list:
        paths = []
        count = 0
        config_path = dir_path
        # Add all config files under config folder (if exists)
        configs_folder = f'{dir_path}/config'
        if os.path.exists(configs_folder):
            for file in os.listdir(configs_folder):
                if os.path.isfile(f'{configs_folder}/{file}') and 'config.yaml' in file:
                    paths.append(f'{configs_folder}/{file}')
        
        while os.path.basename(os.path.dirname(os.path.normpath(config_path))) != 'pulumi' and count < 50:
            if os.path.isfile(f'{config_path}/config.yaml'):
                paths.append(f'{config_path}/config.yaml')
            config_path += '/..'
            count += 1
        
        return paths
    
    @staticmethod
    def __merge(yaml1, yaml2):
        if isinstance(yaml1,dict) and isinstance(yaml2,dict):
            for k,v in yaml2.items():
                if k not in yaml1:
                    yaml1[k] = v
                else:
                    yaml1[k] = GlobalUtils.__merge(yaml1[k],v)
        return yaml1

    @staticmethod
    def merge_yaml_files(config_paths: list):
        merged_yaml = {}

        if len(config_paths) > 0:
            with open(config_paths[0], 'r') as f:
                merged_yaml = yaml.safe_load(f)

        for index, file_path in enumerate(config_paths):
            if index > 0:
                with open(file_path, 'r') as f:
                    yaml2 = yaml.safe_load(f)
                merged_yaml = GlobalUtils.__merge(yaml1=merged_yaml, yaml2=yaml2)

        try:
            validate(instance=merged_yaml, schema=config_schema)
        except Exception as e:
            raise Exception(f'Config validation failed! make sure your united config is like the schema! error: {e}')
        
        # update the dict to be access from anywhere
        GlobalUtils.config_dict = merged_yaml
        return merged_yaml
    
    @staticmethod
    def get_project_url(dir_path: str):
        projects_url = []
        for folder in os.listdir(f'{dir_path}/projects'):
            if folder != '__pycache__':
                with open(f'{dir_path}/projects/{folder}/config.yaml', 'r') as f:
                    tenant_config = yaml.safe_load(f)
                    projects_url.append(tenant_config['tenant']['url'])
        
        return projects_url