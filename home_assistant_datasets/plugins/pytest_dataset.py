"""Pytest plugin for configuring a dataset in use during a test.

This configures a commandline flag `--dataset` that determines which
dataset is under test.
"""

import pathlib
import logging
import pytest

from home_assistant_datasets.datasets.dataset_card import DatasetCard, read_dataset_card

_LOGGER = logging.getLogger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Pytest arguments passed when reading from a dataset for scraping."""
    parser.addoption(
        "--dataset",
        required=False,
        help="The path to the 'assist' style dataset to load for scraping.",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate test parameters for dataset reading from flags."""
    dataset = metafunc.config.getoption("dataset")
    if not dataset:
        raise ValueError("No dataset path specified")
    metafunc.parametrize("dataset", [dataset], scope="module")


@pytest.fixture(scope="module")
def dataset_card(dataset: str) -> DatasetCard:
    return read_dataset_card(pathlib.Path(dataset))
