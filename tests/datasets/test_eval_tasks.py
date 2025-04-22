"""Tests to validate the format of the eval tasks in datasets."""

import pathlib

import pytest

from home_assistant_datasets.datasets.dataset_card import read_dataset_card
from home_assistant_datasets.datasets.assist_eval_task import generate_assist_eval_tasks
from home_assistant_datasets.datasets.assist_data_loader import read_dataset_records

DATASETS = [
    "assist",
    "assist-mini",
    "automations",
]


DATASET_PATH = pathlib.Path("datasets/")
IGNORE_FILES = {"__pycache__"}
DATASET_PATHS = [DATASET_PATH / dataset for dataset in DATASETS]


@pytest.mark.parametrize(
    "dataset", DATASET_PATHS, ids=[str(path) for path in DATASET_PATHS]
)
def test_eval_tasks(dataset: str) -> None:
    """Test the format of the record files."""
    for record in read_dataset_records(read_dataset_card(dataset)):
        for eval_task in generate_assist_eval_tasks(record):
            assert eval_task.input_text
            assert eval_task.category
            assert eval_task.task_num is None


def test_assert_task_num() -> None:
    """Test that we can generate multiple tasks for a single record."""
    record = next(read_dataset_records(read_dataset_card(DATASET_PATHS[0])))
    task_iter = generate_assist_eval_tasks(record, 2)

    # Two instances of the first record in the dataset
    eval_task = next(task_iter)
    assert eval_task.task_num == 0
    eval_task = next(task_iter)
    assert eval_task.task_num == 1

    # Two instances of the second record in the dataset
    eval_task = next(task_iter)
    assert eval_task.task_num == 0
    eval_task = next(task_iter)
    assert eval_task.task_num == 1
