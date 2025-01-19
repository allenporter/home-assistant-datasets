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
from typing import Any
import pathlib
import logging
from functools import cache

_LOGGER = logging.getLogger(__name__)

DEFAULT_SECRETS_FILE = "secrets.yaml"
SECRETS_FILE = pathlib.Path(os.environ.get("SECRETS_FILE", DEFAULT_SECRETS_FILE))


@cache
def _get_secrets() -> dict[str, Any]:
    """Load the secrets from disk."""
    secrets = yaml.load(open(SECRETS_FILE), Loader=yaml.Loader)
    return secrets or {}


def get_secret(secret_name: str) -> str:
    """Get secret with the specified name."""
    secrets = _get_secrets()
    if secret_name not in secrets:
        _LOGGER.debug(
            "Could not find secret_name %s in keys (%s)", secret_name, secrets.keys()
        )
        raise KeyError(
            f"Could not find '{secret_name}' in secrets file {SECRETS_FILE.resolve()}"
        )
    return str(secrets[secret_name])
