"""Common librarys for collecting model outputs for evaluation."""

from typing import Any
import pathlib
from dataclasses import dataclass
import yaml

from . import yaml_loaders


MODEL_CONFIG_FILE = pathlib.Path("models.yaml")


@dataclass
class ModelConfig:
    """The configuration for the conversation agent under evaluation."""

    model_id: str
    """Details about the model name being evaluated if the domain supports multiple models."""

    domain: str
    """The domain under evaluation."""

    description: str
    """A detailed description of the model tested."""

    url: list[str] | None = None
    """A list of relevant urls for the model and its serving infrastructure."""

    config_entry_data: dict[str, Any] | None = None
    """The configuration entry data."""

    config_entry_options: dict[str, Any] | None = None
    """The configuration entry options."""

    version: int | None = None
    """The version number of the config entry."""


@dataclass
class Models:
    """The configuration for the full set of models in the config file."""

    models: list[ModelConfig]
    """The list of models under configuration"""


def read_models() -> Models:
    """Read models configuration file."""
    with MODEL_CONFIG_FILE.open() as fd:
        try:
            model_data = yaml.load(fd.read(), Loader=yaml_loaders.FastSafeLoader)
        except Exception as err:
            raise ValueError(f"Error while loading {MODEL_CONFIG_FILE}: {err}")

    models = model_data.get("models", [])
    return Models(
        models=[
            ModelConfig(**model)
            for model in models
        ]
    )


def read_model(model_id: str) -> ModelConfig:
    """Read a specific model from the config file."""
    models = read_models()
    for model in models.models:
        if model.model_id == model_id:
            return model

    raise ValueError(
        f"Model config file '{MODEL_CONFIG_FILE}' did not contain model_id: {model_id}"
    )
