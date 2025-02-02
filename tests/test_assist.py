"""Tests to validate the format of the assist datasets."""

import pathlib

import pytest

from home_assistant_datasets.tool import data_model


DATASET_PATH = pathlib.Path("datasets/assist/")
IGNORE_FILES = {
    "_fixtures.yaml",
    "dataset_card.yaml",
}
TEST_FILES = [
    filename
    for filename in DATASET_PATH.glob("**/*.yaml")
    if filename.name not in IGNORE_FILES
]


@pytest.mark.parametrize(
    ("filename"), TEST_FILES, ids=(str(filename) for filename in TEST_FILES)
)
def test_eval_tasks(filename: pathlib.Path) -> None:
    """Test the format of the record files."""
    eval_tasks = list(
        data_model.generate_tasks(
            filename, DATASET_PATH, pathlib.Path("/dev/null"), {"example"}
        )
    )
    for eval_task in eval_tasks:
        assert eval_task.output_dir
        assert eval_task.input_text
        assert eval_task.category
