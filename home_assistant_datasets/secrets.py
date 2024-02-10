"""Library for loading secrets from secrets.yaml file."""
import yaml
import os

DEFAULT_SECRETS_FILE = "secrets.yaml"

def get_secret(secret_name: str) -> str:
    """Get secret."""
    secrets_file = os.environ.get("SECRETS_FILE", DEFAULT_SECRETS_FILE)
    secrets = yaml.load(open(secrets_file), Loader=yaml.Loader)
    return secrets[secret_name]
