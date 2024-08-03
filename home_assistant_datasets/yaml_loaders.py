"""Initialize the yaml_loaders extensions."""

from pathlib import Path
from typing import Any, TypeVar, Type

import yaml
from mashumaro.codecs.yaml import YAMLDecoder

from . import secrets

T = TypeVar("T")

_DEFAULT_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


class FastSafeLoader(_DEFAULT_LOADER):
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


def _default_decoder(stream: Any) -> Any:
    """Decode a YAML document using the custom tag constructors."""
    return yaml.load(stream, Loader=FastSafeLoader)


def yaml_decode(stream: Any, shape_type: Type[T] | Any) -> T:
    """Decode a YAML document using the custom tag constructors.

    This function is comparable to the mashumaro.codecs.yaml.yaml_decode function,
    but accepts a stream rather than content string in order to implement
    custom tags based on the current filename.
    """
    return YAMLDecoder(shape_type, pre_decoder_func=_default_decoder).decode(stream)


def _include_tag_constructor(
    loader: yaml.SafeLoader, node: yaml.nodes.ScalarNode
) -> Any:
    """Load a file from the filesystem."""
    path = Path(node.value)
    if not path.is_absolute():
        loader_path = Path(loader.name)
        if not loader_path.exists():
            raise FileNotFoundError(
                f"Could not determine yaml file path from '{loader_path}'"
            )
        path = loader_path.parent / path

    if not path.exists():
        raise FileNotFoundError(f"File '{path}' does not exist {str(node.start_mark)}")

    if not path.is_file():
        raise FileNotFoundError(f"File '{path}' is not a file {str(node.start_mark)}")

    with path.open() as include_file:
        return yaml.load(include_file, Loader=FastSafeLoader)


def _get_secret_constructor(
    loader: yaml.SafeLoader, node: yaml.nodes.ScalarNode
) -> Any:
    """Load a file from the filesystem."""
    setcret_name = node.value
    return secrets.get_secret(setcret_name)


# Register the custom tag constructors.
FastSafeLoader.add_constructor("!include", _include_tag_constructor)
FastSafeLoader.add_constructor("!secret", _get_secret_constructor)
