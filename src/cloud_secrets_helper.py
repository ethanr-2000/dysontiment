from google.cloud import secretmanager
import logging


class CloudSecretsHelper:
    def __init__(self, project_path, credentials=None):
        if credentials is not None:
            self.client = secretmanager.SecretManagerServiceClient(credentials=credentials)
        else:
            self.client = secretmanager.SecretManagerServiceClient()
        self.client.project_path(project_path)

    def get_secret(self, secret_id):
        try:
            secret = self.client.access_secret_version(secret_id)
            logging.info("Secret {} retrieved successfully".format(secret_id))
        except Exception as e:
            logging.critical("Could not retrieve secret | ID: {}".format(secret_id))
            logging.critical(e)
            raise e
        return secret.payload.data.decode("utf-8")
