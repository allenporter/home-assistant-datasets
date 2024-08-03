"""Data collection test fixtures."""

import pathlib
import logging
import datetime
from typing import Any
from collections.abc import Generator

import pytest
from homeassistant.util import dt as dt_util

from .data_model import (
    EvalTask,
    generate_tasks,
)

_LOGGER = logging.getLogger(__name__)


def pytest_addoption(parser: Any) -> None:
    """Pytest arguments passed from the `collect` action to the test."""
    parser.addoption("--dataset")
    parser.addoption("--models")
    parser.addoption("--model_output_dir")
    parser.addoption("--categories")


def pytest_generate_tests(metafunc: Any) -> None:
    """Generate test parameters for the evaluation from flags."""
    # Parameterize tests by the models under development
    models = metafunc.config.getoption("models").split(",")
    metafunc.parametrize("model_id", models)

    output_dir = metafunc.config.getoption("model_output_dir")

    # Load the datasets
    dataset = metafunc.config.getoption("dataset")
    if not dataset:
        raise ValueError("No dataset path specified")

    # Tests are parameterized by the files that contain device actions. Ignore
    # fixtures and load those separately below.
    dataset_files = [
        str(filename)
        for filename in pathlib.Path(dataset).glob("**/*.yaml")
        if filename.name != "_fixtures.yaml"
    ]
    if not dataset_files:
        raise ValueError(f"Could not find any dataset files in path: {dataset}")

    categories_str = metafunc.config.getoption("categories")
    categories = set(categories_str.split(",") if categories_str else {})

    dataset_path = pathlib.Path(dataset)
    output_path = pathlib.Path(output_dir)

    tasks = []
    for record_filename in dataset_files:
        record_path = pathlib.Path(record_filename)

        try:
            eval_tasks = list(
                generate_tasks(record_path, dataset_path, output_path, categories)
            )
        except (ValueError, AttributeError, LookupError) as err:
            raise ValueError(
                f"Task record file '{str(record_path)}' was invalid: {err}"
            ) from err
        tasks.extend(eval_tasks)

    metafunc.parametrize(
        "eval_task", [pytest.param(task, id=task.task_id) for task in tasks]
    )


@pytest.fixture(autouse=True)
def restore_tz() -> Generator[None, None]:
    yield
    # Home Assistant teardown seems to run too soon and expects this so try to
    # patch it in first.
    dt_util.set_default_time_zone(datetime.UTC)


@pytest.fixture(name="eval_output_file")
def eval_output_file_fixture(model_id: str, eval_task: EvalTask) -> pathlib.Path:
    """Sets the output filename for the evaluation run.

    This output file needs to be unique across the test instances to avoid overwriting. For
    example if you add a parameter based on the system prompt then this needs to create
    a separate file containing an id of the prompt.
    """
    return pathlib.Path(f"{eval_task.output_dir}/{model_id}/{eval_task.task_id}.yaml")


@pytest.fixture(name="synthetic_home_yaml")
def mock_synthetic_home_content(eval_task: EvalTask) -> str | None:
    """Mock out the yaml config file contents."""
    return eval_task.synthetic_home_yaml
