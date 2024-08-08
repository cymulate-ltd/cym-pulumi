from components.clouds.aws.secret_manager import SecretManager

class SecretManagerUtils:

    @staticmethod
    def secret_manager_handler(secret_manager: SecretManager, secret_manager_dict: dict, iam_dict: dict):
        for secret_key in secret_manager_dict.keys():
            secret_dict = secret_manager_dict[secret_key]
        
            if secret_dict.get('reference_policy'):
                secret_value = secret_manager.get_secret_value(
                    secret_arn=secret_dict['reference_arn'])
                update_dict = secret_dict.get('update_json_secret_vars', {})
                secret_arn = secret_manager.create_json_secret(
                    name=secret_dict['name'], json_secret_value=secret_value, update_dict=update_dict
                )
                # updating the original dict and populating the secret_arn field
                iam_dict['policies'][secret_dict['reference_policy']]['template_vars']['resource_arn'] = secret_arn
                