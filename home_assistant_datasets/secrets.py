"""Library for loading secrets from secrets.yaml file.

This will read secrets from a `secrets.yaml` file or whatever filename
is referenced by the environment variable `SECRETS_FILE`.

The secrets file is a yaml key/value pair like this:

```yaml
---
google_api_key: XXXXXXXXXXXXXXXXXXXX
openai_api_key: sk-XXXXXXXXXXXXXXXXXXXX
vicuna_convesation_base_url: http://llama-cublas.llama:8000/v1
```

A secrets file is ignored by `.gitignore` allowing you to check in the code
for most of your git repo but leaving your secrets local.
"""

import yaml
import os
import pathlib
import logging

_LOGGER = logging.getLogger(__name__)

DEFAULT_SECRETS_FILE = "secrets.yaml"


def get_secret(secret_name: str) -> str:
    """Get secret with the specified name."""
    secrets_file = pathlib.Path(os.environ.get("SECRETS_FILE", DEFAULT_SECRETS_FILE))
    secrets = yaml.load(open(secrets_file), Loader=yaml.Loader)
    if secret_name not in secrets:
        _LOGGER.debug(
            "Could not find secret_name %s in keys (%s)", secret_name, secrets.keys()
        )
        raise KeyError(f"Could not find '{secret_name}' in secrets file {secrets_file.resolve()}")
    return str(secrets[secret_name])
