"""Data collection test fixtures."""

import pathlib
import logging
import datetime
from typing import Any
from collections.abc import Generator, Callable, Awaitable
import enum
from typing import cast

import yaml
import pytest
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant, Context
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er, llm
from homeassistant.components.conversation import trace

from home_assistant_datasets.data_model import DATASET_CARD_FILE, read_dataset_card

from home_assistant_datasets.tool.data_model import (
    EvalTask,
    generate_tasks,
    EntityState,
)

_LOGGER = logging.getLogger(__name__)

PLUGINS = [
    "home_assistant_datasets.fixtures",
]
IGNORE_FILES = {
    "_fixtures.yaml",
    "_home.yaml",
    DATASET_CARD_FILE,
}


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
    metafunc.parametrize("model_id", models, scope="module")

    output_dir = metafunc.config.getoption("model_output_dir")

    # Load the datasets
    dataset = metafunc.config.getoption("dataset")
    if not dataset:
        raise ValueError("No dataset path specified")
    metafunc.parametrize("dataset", [dataset], scope="module")

    dataset_path = pathlib.Path(dataset)
    dataset_card = read_dataset_card(dataset_path / DATASET_CARD_FILE)
    if dataset_card.path:
        # The dataset card points to files in another directory
        dataset_path = pathlib.Path(dataset_card.path)

    # Tests are parameterized by the files that contain device actions. Ignore
    # fixtures and load those separately below.
    dataset_files = [
        str(filename)
        for filename in dataset_path.glob("**/*.yaml")
        if filename.name not in IGNORE_FILES
    ]
    if not dataset_files:
        raise ValueError(f"Could not find any dataset files in path: {dataset}")

    categories_str = metafunc.config.getoption("categories")
    categories = set(categories_str.split(",") if categories_str else {})

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
def restore_tz() -> Generator[None, None, None]:
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


@pytest.fixture(name="get_state")
def get_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> Callable[[], dict[str, EntityState]]:
    """Fixture with a function call to change device state for evaluation."""

    def func() -> dict[str, EntityState]:
        entity_entries = er.async_entries_for_config_entry(
            entity_registry, synthetic_home_config_entry.entry_id
        )
        results = {}
        for entity_entry in entity_entries:
            state = hass.states.get(entity_entry.entity_id)
            assert state
            assert state.state
            assert state.attributes
            results[entity_entry.entity_id] = EntityState(
                state=state.state, attributes=dict(state.attributes)
            )
            assert state.state not in (
                "unavailable",
                "unknown",
            ), f"Entity id has unavailable state {entity_entry.entity_id}: {state.state}"

        return results

    return func


def compare_state(v: Any, other_v: Any) -> bool:
    """Compare values for equivalence."""
    # Coerce some equivalent types for simpler comparisons
    if isinstance(v, tuple) or isinstance(other_v, tuple):
        v = list(v)
        other_v = list(v)
        return cast(bool, v == other_v)

    if isinstance(v, enum.StrEnum) or isinstance(other_v, enum.StrEnum):
        v = str(v)
        other_v = str(other_v)
        return cast(bool, v == other_v)

    if v == other_v:
        return True

    if str(v) == str(other_v):
        return True

    return False


def compute_entity_diff(
    a_state: EntityState, b_state: EntityState, ignored: set[str]
) -> dict[str, Any] | None:
    """Compute a diff between two entity states."""
    a = a_state.as_dict()
    b = b_state.as_dict()

    diff_attributes = set([])
    for k, v in a.items():
        other_v = b.get(k)
        if not compare_state(other_v, v):
            diff_attributes.add(k)
    for k in b:
        if k not in a and k:
            diff_attributes.add(k)
    diff_attributes = set({k for k in diff_attributes if k not in ignored})
    if not diff_attributes:
        return None
    return {
        "expected": {key: a.get(key) for key in diff_attributes},
        "got": {key: b.get(key) for key in diff_attributes},
    }


@pytest.fixture(name="verify_state")
async def verify_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> Callable[
    [EvalTask, dict[str, EntityState], dict[str, EntityState]],
    Awaitable[dict[str, Any]],
]:
    """Fixture that will verify the device state is in the expected state."""

    async def func(
        task: EvalTask,
        states: dict[str, EntityState],
        updated_states: dict[str, EntityState],
    ) -> dict[str, Any]:
        # Update states to what is expected
        for entity_id, entity_state in (task.expect_changes or {}).items():
            if entity_id not in states:
                raise ValueError(
                    f"Entity defined in eval task does not exist: {entity_id}"
                )
            if entity_state.state is not None:
                states[entity_id].state = entity_state.state
            if entity_state.attributes is not None:
                if states[entity_id].attributes is None:
                    states[entity_id].attributes = {}
                states[entity_id].attributes = {
                    **states[entity_id].attributes,  # type: ignore[dict-item]
                    **entity_state.attributes,
                }

        for entity_id in updated_states:
            if entity_id not in states:
                raise ValueError(f"Unexpected new entity found: {entity_id}")

        diffs = {}
        for entity_id in states:
            ignored_attributes = (
                set(task.ignore_changes.get(entity_id, []))
                if task.ignore_changes
                else set({})
            )
            old = states[entity_id]
            new = updated_states[entity_id]
            if diff := compute_entity_diff(old, new, ignored_attributes):
                diffs[entity_id] = diff
        return diffs

    return func


def dump_conversation_trace(trace: trace.ConversationTrace) -> list[dict[str, Any]]:
    """Serialize the conversation trace for evaluation."""
    trace_data = trace.as_dict()
    trace_events = trace_data["events"]
    result = []
    for trace_event in trace_events:
        trace_event_data = trace_event["data"]
        data = {}
        for k, v in trace_event_data.items():
            if isinstance(v, Context):
                v = dict(v.as_dict())
            if isinstance(v, list) and v and isinstance(v[0], llm.Tool):
                v = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": str(tool.parameters),
                    }
                    for tool in v
                ]
            data[k] = v
        result.append(
            {
                "event_type": str(trace_event["event_type"]),
                "data": data,
            }
        )
    return result

def _configure_yaml() -> None:
    """Configure pyyaml with some formatting options specific to our eval records."""

    # Skip any output for unknown tags
    yaml.emitter.Emitter.prepare_tag = lambda self, tag: ""  # type: ignore[method-assign]

    # Make automation dumps look a little nicer in the output reports
    def str_presenter(dumper, data):  # type: ignore[no-untyped-def]
        """configures yaml for dumping multiline strings
        Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data
        """
        if data.count("\n") > 0:  # check for multiline string
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


def run_pytest_main(additional_args: list[str], directory: str) -> int:
    """Run pytest with the default set of arguments plus the additional args passed."""

    _configure_yaml()

    # nest_asyncio.apply()
    pytest_args = [
        "--no-header",
        "--disable-warnings",
        # Limit to tests in this directory
        directory,
        *additional_args,
    ]
    retcode = pytest.main(
        pytest_args,
        plugins=PLUGINS,
    )
    return retcode
