"""Common librarys for collecting model outputs for evaluation."""

from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any
import pathlib

from slugify import slugify
import yaml

from . import yaml_loaders


MODEL_CONFIG_FILE = pathlib.Path("models.yaml")
MODEL_CONFIG_DIR = pathlib.Path("models")
DATASET_CARD_FILE = "dataset_card.yaml"
DATASET_CARD_FILES = sorted(
    list(pathlib.Path("datasets").glob(f"**/{DATASET_CARD_FILE}"))
)
DATASET_TASK_IGNORE_FILES = {
    "_fixtures.yaml",
    "_home.yaml",
    "solution.yaml",
    DATASET_CARD_FILE,
}
# Label used to keep around configuration but not use for latest metric calculations
ARCHIVED_LABEL = "archived"


@dataclass(kw_only=True)
class DatasetCard:
    """A description of a dataset."""

    name: str
    """The name of the dataset."""

    description: str
    """A detailed description of the dataset."""

    urls: list[str]
    """More information about the dataset."""

    count: int | None = None
    """Number of times to run each task by default."""

    version: str | None = None
    """Current version of the dataset."""

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

    categories: list[str] = field(default_factory=list)
    """Arbitrary labels about this model."""


@dataclass
class Models:
    """The configuration for the full set of models in the config file."""

    models: list[ModelConfig]
    """The list of models under configuration"""

    prerequisites: list[EntryConfig]
    """The prerequisites for the models under evaluation."""


@lru_cache
def read_models() -> Models:
    """Read models configuration file."""
    if MODEL_CONFIG_FILE.exists():
        model_config_content = MODEL_CONFIG_FILE.open()
        try:
            models: Models = yaml_loaders.yaml_decode(model_config_content, Models)
        except Exception as err:
            raise ValueError(f"Error while loading {MODEL_CONFIG_FILE}: {err}")
    else:
        models = Models(models=[], prerequisites=[])

    for model_file in sorted(list(MODEL_CONFIG_DIR.glob("**/*.yaml"))):
        try:
            model_config = yaml_loaders.yaml_decode(model_file.open(), ModelConfig)
        except Exception as err:
            raise ValueError(f"Error while loading {model_file}: {err}")
        if "archive" in str(model_file):
            model_config.categories.append(ARCHIVED_LABEL)
        models.models.append(model_config)

    return models


def read_model(model_id: str) -> ModelConfig:
    """Read a specific model from the config file."""
    models = read_models()
    for model in models.models:
        if model.model_id == model_id:
            return model

    raise ValueError(
        f"Model config file '{MODEL_CONFIG_FILE}' did not contain model_id: {model_id}"
    )


@lru_cache
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


def _make_slug(text: str) -> str:
    """Shorthand slugify command"""
    return slugify(text, separator="_")


def read_dataset_files(dataset_path: pathlib.Path) -> dict[str, pathlib.Path]:
    """Generate the list of dataset files for the given path."""

    dataset_card = read_dataset_card(dataset_path / DATASET_CARD_FILE)
    if dataset_card.path:
        # The dataset card points to files in another directory
        dataset_path = pathlib.Path(dataset_card.path)

    def record_id(filename: pathlib.Path) -> str:
        return _make_slug(str(filename.relative_to(dataset_path))[:-5])

    # Tests are parameterized by the files that contain device actions. Ignore
    # fixtures and load those separately below.
    dataset_files = {
        record_id(filename): filename
        for filename in dataset_path.glob("**/*.yaml")
        if filename.name not in DATASET_TASK_IGNORE_FILES
    }
    if not dataset_files:
        raise ValueError(
            f"Could not find any dataset files in path: {str(dataset_path)}"
        )

    return dataset_files
