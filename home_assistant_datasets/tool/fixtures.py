"""Data collection test fixtures."""

from collections.abc import Generator, Callable, Awaitable
import datetime
import enum
import getpass
from importlib.metadata import version
import pathlib
import logging
from typing import Any
from typing import cast
from unittest.mock import patch
import sys
import uuid

import yaml
import pytest
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant, Context
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr, entity_registry as er, llm
from homeassistant.components.conversation import trace, async_converse

from home_assistant_datasets.data_model import (
    read_dataset_files,
    read_dataset_card,
    DATASET_CARD_FILE,
)

from home_assistant_datasets.tool.data_model import (
    EvalTask,
    generate_tasks,
    EntityState,
    TokenStats,
    TokenStatsBank,
    ScrapeContext,
    ScrapeConfig,
    SCRAPE_CONTEXT_FILE,
)


_LOGGER = logging.getLogger(__name__)

PLUGINS = [
    "home_assistant_datasets.fixtures",
    "home_assistant_datasets.tool.fixtures",
]


def pytest_addoption(parser: Any) -> None:
    """Pytest arguments passed from the `collect` action to the test."""
    parser.addoption("--dataset")
    parser.addoption("--models")
    parser.addoption("--model_output_dir")
    parser.addoption("--categories")
    parser.addoption("--count")


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

    # Tests are parameterized by the files that contain device actions. Ignore
    # fixtures and load those separately below.
    dataset_path = pathlib.Path(dataset)
    dataset_files = read_dataset_files(dataset_path)
    dataset_card = read_dataset_card(dataset_path / DATASET_CARD_FILE)

    categories_str = metafunc.config.getoption("categories")
    categories = set(categories_str.split(",") if categories_str else {})
    if count := metafunc.config.getoption("count"):
        count = int(count)
    else:
        count = dataset_card.count

    output_path = pathlib.Path(output_dir)
    metafunc.parametrize(
        "output_path", [pytest.param(output_path, id="output_path")], scope="module"
    )

    tasks = []
    for record_id, record_path in dataset_files.items():

        try:
            eval_tasks = list(generate_tasks(record_id, record_path, categories, count))
        except (ValueError, AttributeError, LookupError) as err:
            raise ValueError(
                f"Task record file '{str(record_path)}' was invalid: {err}"
            ) from err
        tasks.extend(eval_tasks)

    metafunc.parametrize(
        "eval_task", [pytest.param(task, id=task.task_id) for task in tasks]
    )


@pytest.fixture(name="scrape_config", scope="module")
def scrape_config(model_id: str, dataset: str, output_path: str) -> ScrapeConfig:
    """Fixture to generate a scrape config."""
    dataset_path = pathlib.Path(dataset)
    dataset_card = read_dataset_card(dataset_path / DATASET_CARD_FILE)
    return ScrapeConfig(
        dataset=dataset_card.name,
        dataset_path=str(dataset_path),
        model_id=model_id,
        model_output_path=str(output_path),
    )


def create_scrape_context(scrape_config: ScrapeConfig) -> ScrapeContext:
    """Fixture to generate a scrape record."""
    home_assistant_version = version("homeassistant")
    context: dict[str, Any] = {"user": getpass.getuser() or "unknown"}
    if sys.argv:
        context["argv"] = sys.argv
    return ScrapeContext(
        uuid=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(),
        version=home_assistant_version,
        scrape_config=scrape_config,
        context=context,
        notes="",
    )


@pytest.fixture(name="scrape_record_writer", scope="module", autouse=True)
def scrape_record_writer_fixture(scrape_config: ScrapeConfig) -> None:
    """Fixture to generate a scrape record."""
    scrape_context = create_scrape_context(scrape_config)
    output = scrape_config.scrape_output_path / SCRAPE_CONTEXT_FILE
    output.parent.mkdir(exist_ok=True)
    output.write_text(yaml.dump(scrape_context, sort_keys=False, explicit_start=True))


@pytest.fixture(autouse=True)
def restore_tz() -> Generator[None, None, None]:
    yield
    # Home Assistant teardown seems to run too soon and expects this so try to
    # patch it in first.
    dt_util.set_default_time_zone(datetime.UTC)


@pytest.fixture(name="eval_output_file")
def eval_output_file_fixture(
    scrape_config: ScrapeConfig, eval_task: EvalTask
) -> pathlib.Path:
    """Sets the output filename for the evaluation run.

    This output file needs to be unique across the test instances to avoid overwriting. For
    example if you add a parameter based on the system prompt then this needs to create
    a separate file containing an id of the prompt.
    """
    return scrape_config.eval_task_output_path(eval_task.task_id)


@pytest.fixture(name="context_now", autouse=True)
def context_now_fixture(
    eval_task: EvalTask,
) -> Generator[datetime.datetime | None, None, None]:
    """Fixture to set "now" based on the eval task context."""
    if eval_task.context_now is None:
        yield None
        return

    with patch(
        "homeassistant.util.dt.now", return_value=eval_task.context_now
    ) as now_dt:
        yield now_dt


@pytest.fixture(name="context_device_id")
def context_device_id_fixture(
    synthetic_home_config_entry: Any,
    device_registry: dr.DeviceRegistry,
    eval_task: EvalTask,
) -> str | None:
    """Fixture to return the Homoe Assistant device id for the current context."""
    if eval_task.context_device is None:
        return None
    device_entries = dr.async_entries_for_config_entry(
        device_registry, synthetic_home_config_entry.entry_id
    )
    device_entry_map = {
        identifier[1]: device_entry
        for device_entry in device_entries
        for identifier in device_entry.identifiers
    }
    if context_device_entry := device_entry_map.get(eval_task.context_device):
        return context_device_entry.id
    raise ValueError(
        f"Could not find context device '{eval_task.context_device}' in synthetic home {synthetic_home_config_entry}: {device_entry_map}"
    )


@pytest.fixture(name="patch_device_id", autouse=True)
def patch_device_id_fixture(context_device_id: str | None) -> Generator[None]:
    """Fixture to insert the LLM context device_id argument to the start of the conversation."""

    if context_device_id is None:
        yield
        return

    original_function = async_converse

    async def add_device_id(*args: Any, **kwargs: Any) -> Any:
        kwargs["device_id"] = context_device_id
        return await original_function(*args, **kwargs)

    with patch(
        "homeassistant.components.conversation.async_converse",
        side_effect=add_device_id,
    ):
        yield


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
        values: dict[str, Any] = {
            "event_type": str(trace_event["event_type"]),
            "data": data,
        }
        if ts_str := trace_event.get("timestamp"):
            values["timestamp"] = datetime.datetime.fromisoformat(ts_str)
        result.append(values)
    return result


def find_llm_call(trace_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Gets the llm call from the conversation trace."""
    tool_call = next(
        iter(
            event
            for event in trace_events
            if event["event_type"]
            # type: ignore[attr-defined]
            in (trace.ConversationTraceEventType.TOOL_CALL, "llm_tool_call")
        ),
        None,
    )
    if tool_call is None:
        return None

    data = tool_call["data"]
    return {
        "tool_name": data.get("tool_name"),
        "tool_args": data.get("tool_args"),
    }


def find_token_stats(trace_events: list[dict[str, Any]]) -> TokenStats | None:
    """Gets the agent detail that contains conversation agent statistics."""
    stats_data = list(
        stats
        for event in trace_events
        if event["event_type"] == trace.ConversationTraceEventType.AGENT_DETAIL
        and (stats := event["data"].get("stats")) is not None
    )
    if not stats_data:
        return None
    bank = TokenStatsBank()
    for stats in stats_data:
        bank.append(
            TokenStats(
                input_tokens=stats.get("input_tokens", 0),
                cached_input_tokens=stats.get("cached_input_tokens", 0),
                output_tokens=stats.get("output_tokens", 0),
            )
        )
    return bank.sum()


def configure_yaml() -> None:
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

    configure_yaml()

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
