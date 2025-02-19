"""Tests to validate the format of the automation datasets."""

import pathlib

import pytest


DATASET_PATH = pathlib.Path("datasets/automations/")
IGNORE_FILES = {"__pycache__"}
PROBLEM_DIRS = [
    child
    for child in DATASET_PATH.iterdir()
    if child.is_dir() and child.name not in IGNORE_FILES
]


@pytest.mark.parametrize(
    ("filename"), PROBLEM_DIRS, ids=(str(filename) for filename in PROBLEM_DIRS)
)
def test_required_files(filename: pathlib.Path) -> None:
    """Test the format of the record files."""
    assert (filename / "DESCRIPTION.md").is_file()
    assert (filename / "_fixtures.yaml").is_file()
    assert (filename / "solution.yaml").is_file()
