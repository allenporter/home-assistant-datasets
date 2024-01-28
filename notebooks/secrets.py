"""Library for loading secrets from secrets.yaml file."""
import yaml

SECRETS_FILE = "secrets.yaml"

def get_secret(secret_name: str) -> str:
    """Get secret."""
    secrets = yaml.load(open(SECRETS_FILE), Loader=yaml.Loader)
    return secrets[secret_name]
