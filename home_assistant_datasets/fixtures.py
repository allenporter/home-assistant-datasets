"""Test fixtures for evaluations."""

from collections.abc import Generator
import logging
import os
import pathlib
from typing import Any, TextIO

import pytest
import yaml

from homeassistant.core import HomeAssistant

from custom_components import synthetic_home  # noqa: F401

# TODO(#12): Support loading from the custom component or core development environment

from home_assistant_datasets.data_model import (
    EntryConfig,
    DatasetCard,
    DATASET_CARD_FILE,
)

from . import data_model


_LOGGER = logging.getLogger(__name__)


@pytest.fixture
async def prerequisites() -> list[EntryConfig]:
    """Fixture to read the prerequisites yaml."""
    return data_model.read_prerequisites()


@pytest.fixture(scope="module")
async def dataset_card(dataset: str) -> DatasetCard:
    dataset_card = pathlib.Path(dataset) / DATASET_CARD_FILE
    return data_model.read_dataset_card(dataset_card)


class EvalRecordWriter:
    """Writes records to the eval output."""

    def __init__(self, filename: pathlib.Path):
        """Initialize EvalRecordWriter."""
        os.makedirs(filename.parent, exist_ok=True)
        self._eval_output = filename
        self._fd: TextIO | None = None

    def open(self) -> None:
        """Initialize the record writer."""
        self._fd = open(self._eval_output, "w")
        self._records = 0

    def write(self, record: dict[str, Any]) -> None:
        """Write an eval record."""
        assert self._fd
        self._fd.write(yaml.dump(record, sort_keys=False, explicit_start=True))
        self._fd.flush()
        self._records += 1

    def close(self) -> None:
        """Close the evaluation record."""
        _LOGGER.info(
            "Wrote %s summariies to %s",
            self._records,
            self._eval_output,
        )

        if self._fd is not None:
            self._fd.close()
            self._fd = None


@pytest.fixture(name="eval_record_writer")
def eval_record_writer_fixture(
    hass: HomeAssistant,
    eval_output_file: pathlib.Path,
) -> Generator[EvalRecordWriter, None, None]:
    """Fixture that prepares the eval output writer."""
    writer = EvalRecordWriter(eval_output_file)
    writer.open()
    yield writer
    writer.close()
