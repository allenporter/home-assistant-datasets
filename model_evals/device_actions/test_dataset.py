"""Validates that the dataset and referenced synthetic homes are valid."""

import pathlib

import pytest

from .data_model import read_record, generate_tasks, dataset_files


@pytest.mark.parametrize(
    ("filename"),
    [(filename) for filename in dataset_files()],
    ids=[str(filename) for filename in dataset_files()],
)
async def test_validate_dataset(filename: pathlib.Path) -> None:
    """Validate the dataset records and homes are valid."""
    record = read_record(filename)
    async for task in generate_tasks(record):
        pass
