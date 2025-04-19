"""Module for reading datasets as part of scraping model outputs."""

from dataclasses import dataclass, field
from functools import lru_cache
import pathlib
from typing import Any

from mashumaro.mixins.yaml import DataClassYAMLMixin

from home_assistant_datasets.yaml_loaders import yaml_decode

__all__ = [
    "DatasetCard",
    "read_dataset_cards",
    "read_dataset_card",
]

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


@dataclass(kw_only=True)
class DatasetCard(DataClassYAMLMixin):
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
    """Path to use for reading the dataset files, defaults to root directory."""

    config_entry_data: dict[str, Any] | None = field(default=None)
    """Additional config entry data to include in model entry configs for this dataset."""

    config_entry_options: dict[str, Any] | None = field(default=None)
    """Additional config entry options to include in model entry configs for this dataset."""

    @property
    def dataset_path(self) -> pathlib.Path:
        """Path to use for reading dataset files."""
        if not self.path:
            raise ValueError(
                "Dataset Card was not loaded properly, use `read_dataset_card`"
            )
        return pathlib.Path(self.path)

    @property
    def dataset_files(self) -> list[pathlib.Path]:
        """Generate the list of dataset files in the dataset."""
        filenames = [
            filename
            for filename in sorted(list(self.dataset_path.glob("**/*.yaml")))
            if filename.name not in DATASET_TASK_IGNORE_FILES
        ]
        if not filenames:
            raise ValueError(
                f"Could not find any dataset files in path: {str(self.dataset_path)}"
            )
        return filenames


@lru_cache
def read_dataset_card(dataset_path: pathlib.Path) -> DatasetCard:
    """Read a single dastaset configuration file."""
    dataset_card = dataset_path / DATASET_CARD_FILE
    card: DatasetCard = yaml_decode(dataset_card.open(), DatasetCard)
    if card.path is None:
        card.path = str(dataset_path)
    return card


@lru_cache
def read_dataset_cards() -> list[DatasetCard]:
    """Read dataset configuration file."""
    card_files = sorted(list(pathlib.Path("datasets").glob(f"**/{DATASET_CARD_FILE}")))
    return [read_dataset_card(dataset_card.parent) for dataset_card in card_files]
