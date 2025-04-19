"""Pytest plugin for configuring dataset records to load during a test.

This depends on the `pytest_dataset` plugin for configuring the dataset
under test.
"""

import pathlib
from typing import Any
import logging
import pytest
from pytest import Metafunc

import yaml

from .datasets.dataset_card import read_dataset_card
from .datasets.assist_data_loader import read_dataset_records
from .datasets.assist_eval_task import EvalTask, generate_assist_eval_tasks

_LOGGER = logging.getLogger(__name__)


def pytest_addoption(parser: Any) -> None:
    """Pytest arguments passed when reading from a dataset for scraping."""
    # Filter on which dataset record categories to load
    parser.addoption("--categories")
    # Number of times to repeat each task in the dataset
    parser.addoption("--count")


def pytest_generate_tests(metafunc: Metafunc) -> None:
    """Generate test parameters for dataset reading from flags."""

    dataset = metafunc.config.getoption("dataset")
    if not dataset:
        raise ValueError(
            "Missing required plugin dependency 'home_assistant_datasets.pytest_dataset'"
        )

    # The actual "task" that will be scraped is a spoke sentence. We expand the
    # dataset records into these invidiaul tasks.
    dataset_path = pathlib.Path(dataset)
    dataset_card = read_dataset_card(dataset_path)

    categories_str = metafunc.config.getoption("categories")
    categories = set(categories_str.split(",") if categories_str else {})
    if count := metafunc.config.getoption("count"):
        count = int(count)
    else:
        count = dataset_card.count

    tasks: list[EvalTask] = []
    for record in read_dataset_records(dataset_card, categories):
        assert record.record_source is not None
        try:
            eval_tasks = list(generate_assist_eval_tasks(record, count))
        except (ValueError, AttributeError, LookupError) as err:
            raise ValueError(
                f"Task record file '{str(record.record_source.record_path)}' was invalid: {err}"
            ) from err
        tasks.extend(eval_tasks)

    metafunc.parametrize(
        "eval_task", [pytest.param(task, id=task.task_id) for task in tasks]
    )


@pytest.fixture(name="synthetic_home_yaml")
def mock_synthetic_home_content(eval_task: EvalTask) -> str:
    """Merge in synthetic home setup from the evaluation record contents."""
    fixture_path = eval_task.record_source.record_path.parent / "_fixtures.yaml"

    # Find the fixtures for this directory. States will be overridden
    # below.
    synthetic_home_config = fixture_path.read_text()
    synthetic_home_yaml = yaml.load(synthetic_home_config, Loader=yaml.Loader)

    # Override any state data
    entities = synthetic_home_yaml.get("entities", [])
    entities_dict = {entity["id"]: entity for entity in entities}
    for entity_id, entity_state in (eval_task.action.setup or {}).items():
        if (found_entity := entities_dict.get(entity_id)) is None:
            raise ValueError(
                f"Entity `setup` entity id '{entity_id}' found in fixture {fixture_path}"
            )
        if entity_state.state is not None:
            found_entity["state"] = entity_state.state
        if entity_state.attributes is not None:
            found_entity["attributes"] = {
                **(found_entity.get("attributes", {})),
                **entity_state.attributes,
            }
        entities_dict[entity_id] = found_entity
    synthetic_home_yaml["entities"] = list(entities_dict.values())
    yaml_contents = yaml.dump(synthetic_home_yaml, explicit_start=True, sort_keys=False)
    return yaml_contents  # type: ignore[no-any-return]
