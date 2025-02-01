"""Common librarys for collecting model outputs for evaluation."""

from typing import Any
import pathlib
from dataclasses import dataclass, field
import yaml

from . import yaml_loaders


MODEL_CONFIG_FILE = pathlib.Path("models.yaml")
DATASET_CARD_FILE = "dataset_card.yaml"
DATASET_CARD_FILES = list(pathlib.Path("datasets").glob(f"**/{DATASET_CARD_FILE}"))


@dataclass(kw_only=True)
class DatasetCard:
    """A description of a dataset."""

    name: str
    """The name of the dataset."""

    description: str
    """A detailed description of the dataset."""

    urls: list[str]
    """More information about the dataset."""

    path: str | None = field(default=None)
    """Path to use for reading the dataset files instead of the current directory."""

    config_entry_data: dict[str, Any] | None = field(default=None)
    """Additional config entry data to include in model entry configs for this dataset."""

    config_entry_options: dict[str, Any] | None = field(default=None)
    """Additional config entry options to include in model entry configs for this dataset."""

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


@dataclass
class Models:
    """The configuration for the full set of models in the config file."""

    models: list[ModelConfig]
    """The list of models under configuration"""

    prerequisites: list[EntryConfig]
    """The prerequisites for the models under evaluation."""


def read_models() -> Models:
    """Read models configuration file."""
    with MODEL_CONFIG_FILE.open() as fd:
        try:
            model_data = yaml.load(fd.read(), Loader=yaml_loaders.FastSafeLoader)
        except Exception as err:
            raise ValueError(f"Error while loading {MODEL_CONFIG_FILE}: {err}")

    models = model_data.get("models", [])
    prerequisites = model_data.get("prerequisites", [])
    return Models(
        models=[ModelConfig(**model) for model in models],
        prerequisites=[EntryConfig(**prerequisite) for prerequisite in prerequisites],
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


def read_dataset_card(dataset_card: pathlib.Path) -> DatasetCard:
    """Read a single dastaset configuration file."""
    data = yaml.load(dataset_card.read_text(), Loader=yaml.Loader)
    return DatasetCard(**data)


def read_prerequisites() -> list[EntryConfig]:
    """Read the prerequisites for the models under evaluation."""
    return read_models().prerequisites


def read_dataset_cards() -> list[DatasetCard]:
    """Read dataset configuration file."""
    cards = []
    for dataset_card in DATASET_CARD_FILES:
        cards.append(read_dataset_card(dataset_card))
    return cards
