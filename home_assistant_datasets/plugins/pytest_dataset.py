"""Pytest plugin for configuring a dataset in use during a test.

This configures a commandline flag `--dataset` that determines which
dataset is under test.
"""

import pathlib
from typing import Any
import logging
import pytest

from home_assistant_datasets.datasets.dataset_card import DatasetCard, read_dataset_card

_LOGGER = logging.getLogger(__name__)


def pytest_addoption(parser: Any) -> None:
    """Pytest arguments passed when reading from a dataset for scraping."""
    parser.addoption("--dataset")


def pytest_generate_tests(metafunc: Any) -> None:
    """Generate test parameters for dataset reading from flags."""
    dataset = metafunc.config.getoption("dataset")
    if not dataset:
        raise ValueError("No dataset path specified")
    metafunc.parametrize("dataset", [dataset], scope="module")


@pytest.fixture(scope="module")
def dataset_card(dataset: str) -> DatasetCard:
    return read_dataset_card(pathlib.Path(dataset))
