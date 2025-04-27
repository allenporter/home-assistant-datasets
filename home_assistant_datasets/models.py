"""Module related to reading model configuration files."""

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any
import pathlib

from mashumaro.mixins.yaml import DataClassYAMLMixin

from home_assistant_datasets.yaml_loaders import yaml_decode

__all__ = [
    "ModelConfig",
    "Models",
    "EntryConfig",
    "read_models",
    "read_model",
]


MODEL_CONFIG_FILE = pathlib.Path("models.yaml")
MODEL_CONFIG_DIR = pathlib.Path("models/")

ARCHIVE_LABEL = "archive"

@dataclass
class Cost(DataClassYAMLMixin):
    """Cost metrics."""

    input_tokens: float
    """Cost for 1M input tokens."""

    output_tokens: float
    """Cost for 1M output tokens."""

    notes: str | None = None
    """Additional models about model pricing."""


@dataclass
class EntryConfig:
    """The configuration entry for the model under evaluation."""

    domain: str
    """The domain of the entry."""

    config_entry_data: dict[str, Any] | None = None
    """The configuration entry data."""

    config_entry_options: dict[str, Any] | None = None
    """The configuration entry options."""

    version: int | None = None
    """The version number of the config entry."""


@dataclass
class ModelConfig:
    """The configuration for the conversation agent under evaluation."""

    model_id: str
    """Details about the model name being evaluated if the domain supports multiple models."""

    domain: str
    """The domain under evaluation."""

    description: str
    """A detailed description of the model tested."""

    categories: list[str] | None = None
    """Labels tagged on the model for later slicing."""

    urls: list[str] | None = None
    """A list of relevant urls for the model and its serving infrastructure."""

    config_entry_data: dict[str, Any] | None = None
    """The configuration entry data."""

    config_entry_options: dict[str, Any] | None = None
    """The configuration entry options."""

    version: int | None = None
    """The version number of the config entry."""

    rpm: int | None = None
    """Requests per minute allowed for this model."""

    categories: list[str] = field(default_factory=list)
    """Arbitrary labels about this model."""

    cost: Cost | None = None
    """Cost metrics for the model entry."""


@dataclass
class Models(DataClassYAMLMixin):
    """The configuration for the full set of models in the config file."""

    models: list[ModelConfig]
    """The list of models under configuration"""

    prerequisites: list[EntryConfig] = field(default_factory=list)
    """The prerequisites for the models under evaluation."""


@lru_cache
def read_models() -> Models:
    """Read models configuration from config files.

    This will load any needed secrets or includes.
    """
    if MODEL_CONFIG_FILE.exists():
        model_config_content = MODEL_CONFIG_FILE.open()
        try:
            models: Models = yaml_decode(model_config_content, Models)
        except Exception as err:
            raise ValueError(f"Error while loading {MODEL_CONFIG_FILE}: {err}")
    else:
        models = Models(models=[], prerequisites=[])

    if not MODEL_CONFIG_DIR.exists():
        raise ValueError(
            f"Could not find model configuration directory: {str(MODEL_CONFIG_DIR)}"
        )

    for model_file in sorted(list(MODEL_CONFIG_DIR.glob("**/*.yaml"))):
        if ARCHIVE_LABEL in str(model_file):
            continue
        try:
            model_config = yaml_decode(model_file.open(), ModelConfig)
        except Exception as err:
            raise ValueError(f"Error while loading {model_file}: {err}")
        models.models.append(model_config)

    return models


def read_model(model_id: str) -> ModelConfig:
    """Read a specific model configuration from the config files."""
    models = read_models()
    for model in models.models:
        if model.model_id == model_id:
            return model

    raise ValueError(
        f"Model config file '{MODEL_CONFIG_FILE}' did not contain model_id: {model_id} ({models})"
    )


def read_prerequisites() -> list[EntryConfig]:
    """Read the prerequisites for the models under evaluation."""
    return read_models().prerequisites
