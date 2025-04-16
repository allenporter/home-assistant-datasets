"""Tests to validate the format of the eval tasks in datasets."""

import pathlib

import pytest

from home_assistant_datasets.tool.data_model import generate_tasks
from home_assistant_datasets.data_model import read_dataset_files

DATASETS = [
    "assist",
    "assist-mini",
    "automations",
    "questions",
]


DATASET_PATH = pathlib.Path("datasets/")
IGNORE_FILES = {"__pycache__"}
TEST_FILES = {
    (dataset, record_id): filename
    for dataset in DATASETS
    for (record_id, filename) in read_dataset_files(DATASET_PATH / dataset).items()
}


@pytest.mark.parametrize(("dataset", "record_id"), TEST_FILES.keys())
def test_eval_tasks(dataset: str, record_id: str) -> None:
    """Test the format of the record files."""
    eval_tasks = list(
        generate_tasks(
            record_id,
            TEST_FILES[(dataset, record_id)],
            pathlib.Path("/dev/null"),
            {"example"},
        )
    )

    for eval_task in eval_tasks:
        assert eval_task.output_dir
        assert eval_task.input_text
        assert eval_task.category
