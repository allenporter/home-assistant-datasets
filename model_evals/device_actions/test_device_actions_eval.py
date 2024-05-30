"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

from collections.abc import Callable, Awaitable
import logging
import pathlib
import uuid
import dataclasses
import yaml
import difflib
from typing import Any

import pytest
from pytest_subtests import SubTests

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.components.conversation import trace

from model_evals.common.conftest import ConversationAgent, EvalRecordWriter
from model_evals.common.common import HomeAssistantContext

from .data_model import (
    EvalTask,
    Record,
    dataset_files,
    read_record,
    DIR,
    generate_tasks,
    DeviceState,
)

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(
    name="model_id",
    params=[
        "assistant",
        # "gpt-3.5",
        # "gpt-4o",
        # "gemini-1.5-flash",
        # "gemini-pro",
        # "mistral-7b-instruct",
    ],
)
def model_id_fixture(request: pytest.FixtureRequest) -> str:
    """Fiture that defines which model is being evaluated."""
    return request.param


@pytest.fixture(
    name="record_filename",
    params=[(filename) for filename in dataset_files()],
    ids=[str(filename) for filename in dataset_files()],
)
def record_filename_fixture(request: pytest.FixtureRequest) -> str:
    """Fixture that reads the records from the dataset."""
    return request.param


@pytest.fixture(name="eval_output_file")
def eval_output_file_fixture(model_id: str, record_filename: str) -> str:
    """Sets the output filename for the evaluation run.

    This output file needs to be unique across the test instances to avoid overwriting. For
    example if you add a parameter based on the system prompt then this needs to create
    a separate file containing an id of the prompt.
    """
    return pathlib.Path(f"{DIR}/output/{model_id}/{record_filename.name}")


@pytest.fixture(name="record")
def record_fixture(record_filename: pathlib.Path) -> str:
    """Read a record from the dataset."""
    return read_record(record_filename)


@pytest.fixture(name="synthetic_home_config")
def synthetic_home_config_fixture(record: Record) -> str:
    """Fiture that defines the synthetic home configuration to use."""
    return f"{DIR}/homes/{record.home}.yaml"



@pytest.fixture(name="set_state")
async def set_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
) -> Callable[[DeviceState], Awaitable[HomeAssistantContext]]:
    """Fixture with a function call to change device state."""

    async def func(device_state: DeviceState) -> HomeAssistantContext:
        _LOGGER.info(
            "Changing device state for %s to %s",
            device_state.name,
            device_state.state,
        )
        service_data = {
            "config_entry_id": synthetic_home_config_entry.entry_id,
            "device": device_state.name,
            "device_state_key": device_state.state,
        }
        if device_state.area:
            service_data["area"] = device_state.area
        await hass.services.async_call(
            "synthetic_home",
            "set_synthetic_device_state",
            service_data=service_data,
            blocking=True,
        )
        await hass.async_block_till_done()

    return func



@pytest.fixture(name="get_state")
def get_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> Callable[[], dict[str, dict[str, str]]]:
    """Fixture with a function call to change device state for evaluation."""

    def func() -> dict[str, dict[str, str]]:
        entity_entries = er.async_entries_for_config_entry(entity_registry, synthetic_home_config_entry.entry_id)
        results = {}
        for entity_entry in entity_entries:
            state = hass.states.get(entity_entry.entity_id)
            results[entity_entry.entity_id] = {
                "state": state.state,
                **state.attributes,
            }
        return results

    return func


@pytest.fixture(name="prepare_state")
async def prepare_state_fixture(
    hass: HomeAssistant,
    set_state: Callable[[DeviceState], Awaitable[HomeAssistantContext]],
) -> Callable[[EvalTask], Awaitable[HomeAssistantContext]]:
    """Fixture with a function call to change device state for evaluation."""

    async def func(task: EvalTask) -> HomeAssistantContext:
        for device_state in task.device_states:
            await set_state(device_state)
        return HomeAssistantContext()

    return func

def compute_entity_diff(a: dict[str, str], b: dict[str, str]) -> dict[str, Any] | None:
    """Compute a diff between two entity states."""

    diff_attributes = set({})
    for k, v in a.items():
        if b.get(k) != v:
            diff_attributes.add(k)
    for k in b:
        if k not in a:
            diff_attributes.add(k)
    if not diff_attributes:
        return None
    return {
        "expected": {
            key: a.get(key)
            for key in diff_attributes
        },
        "got": {
            key: b.get(key)
            for key in diff_attributes
        }
    }




@pytest.fixture(name="verify_state")
async def verify_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
    set_state: Callable[[DeviceState], Awaitable[HomeAssistantContext]],
) -> Callable[[EvalTask], Awaitable[dict[str, Any]]]:
    """Fixture that will verify the device state is in the expected state."""

    async def func(task: EvalTask, states: dict[str, dict[str, str]], updated_states: dict[str, dict[str, str]]) -> dict[str, Any]:
        # Update states to what is expected
        for entity_id, attributes in task.expected_entity_changes.items():
            if entity_id not in states:
                return {"unexpected_states": f"Entity defined in eval task does not exist: {entity_id}"}

            states[entity_id].update(attributes)

        for entity_id in updated_states:
            if entity_id not in states:
                return {"unexpected_states": f"Unexpected new entity found: {entity_id}"}

        diffs = {}
        for entity_id in states:
            old = states[entity_id]
            new = updated_states[entity_id]
            if diff := compute_entity_diff(old, new):
                diffs[entity_id] = diff
        return {"unexpected_states": diffs}

    return func


async def test_collect_device_actions(
    hass: HomeAssistant,
    agent: ConversationAgent,
    eval_record_writer: EvalRecordWriter,
    subtests: SubTests,
    record: Record,
    get_state: Callable[[], list[dict[str, dict[str, str]]]],
    prepare_state: Callable[[EvalTask], Awaitable[HomeAssistantContext]],
    verify_state: Callable[[EvalTask, HomeAssistantContext], Awaitable[HomeAssistantContext]],
) -> None:
    """Collects model responses for area summaries."""

    i = 0
    async for device_action_task in generate_tasks(record):
        i += 1
        with subtests.test(msg=device_action_task.task_id, i=i):

            # Setup the home for evaluation
            context = await prepare_state(device_action_task)
            states = get_state()

            # Run the conversation agent
            text = device_action_task.input_text
            _LOGGER.debug("Prompt: %s", text)
            try:
                response = await agent.async_process(hass, text)
            except (HomeAssistantError, TypeError) as err:
                response = str(err)
            await hass.async_block_till_done()
            _LOGGER.debug("Response: %s", response)

            updated_states = get_state()

            if (traces := trace.async_get_traces()) and (last_trace := traces[-1]):
                context.conversation_trace = last_trace.as_dict()

            state_check = await verify_state(device_action_task, states, updated_states)
            context.device_context.update(state_check)

            eval_record_writer.write(
                {
                    "uuid": str(uuid.uuid4()),  # Unique based on the model evaluated
                    "task_id": device_action_task.task_id,
                    "task": dataclasses.asdict(device_action_task),
                    "response": response,
                    "context": dataclasses.asdict(context),
                }
            )
