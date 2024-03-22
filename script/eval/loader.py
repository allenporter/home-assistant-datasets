"""Initialize the yaml_loaders extensions."""

from typing import Any

import yaml
from yaml import SafeLoader

from home_assistant_datasets import secrets


class FastSafeLoader(SafeLoader):
    """The fastest available safe loader, either C or Python.

    This exists to support capturing the stream file name in the same way as the
    python yaml loader in order to support !include tags.
    """

    def __init__(self, stream: Any) -> None:
        """Initialize a safe line loader."""
        self.stream = stream

        # Set name in same way as the Python loader does in yaml.reader.__init__
        if isinstance(stream, str):
            self.name = "<unicode string>"
        elif isinstance(stream, bytes):
            self.name = "<byte string>"
        else:
            self.name = getattr(stream, "name", "<file>")

        super().__init__(stream)


def _secret_tag_constructor(
    loader: yaml.SafeLoader, node: yaml.nodes.ScalarNode
) -> Any:
    """Load a secret from the secrets library."""
    return secrets.get_secret(node.value)


# Register the custom tag constructors.
SafeLoader.add_constructor("!secret", _secret_tag_constructor)
