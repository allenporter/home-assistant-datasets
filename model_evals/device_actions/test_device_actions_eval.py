"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

from collections.abc import Callable, Awaitable
import logging
import pathlib
import uuid
import dataclasses

import pytest
from pytest_subtests import SubTests

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
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
)

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(
    name="model_id",
    params=[
        # "gemini-1.5-flash",
        # "gpt-4o",
        "mistral-7b-instruct",
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
    return pathlib.Path(f"{DIR}/output/{model_id}/{record_filename.name}.yaml")


@pytest.fixture(name="record")
def record_fixture(record_filename: pathlib.Path) -> str:
    """Read a record from the dataset."""
    return read_record(record_filename)


@pytest.fixture(name="synthetic_home_config")
def synthetic_home_config_fixture(record: Record) -> str:
    """Fiture that defines the synthetic home configuration to use."""
    return f"{DIR}/homes/{record.home}.yaml"


@pytest.fixture(name="prepare_state")
async def prepare_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> Callable[[EvalTask], Awaitable[HomeAssistantContext]]:
    """Fixture with a function call to change device state for evaluation."""

    async def func(task: EvalTask) -> HomeAssistantContext:
        for device_state in task.device_states:
            _LOGGER.info(
                "Changing device state for %s to %s",
                device_state.name,
                device_state.state,
            )
            await hass.services.async_call(
                "synthetic_home",
                "set_synthetic_device_state",
                service_data={
                    "config_entry_id": synthetic_home_config_entry.entry_id,
                    "area": device_state.area,
                    "device": device_state.name,
                    "device_state_key": device_state.state,
                },
                blocking=True,
            )
            await hass.async_block_till_done()

        return HomeAssistantContext()

    return func


@pytest.mark.parametrize("expected_lingering_timers", [(True)])
async def test_collect_device_actions(
    hass: HomeAssistant,
    agent: ConversationAgent,
    eval_record_writer: EvalRecordWriter,
    subtests: SubTests,
    record: Record,
    prepare_state: Callable[[EvalTask], Awaitable[HomeAssistantContext]],
) -> None:
    """Collects model responses for area summaries."""

    i = 0
    async for device_action_task in generate_tasks(record):
        i += 1
        with subtests.test(msg=device_action_task.task_id, i=i):

            # Setup the home for evaluation
            context = await prepare_state(device_action_task)

            # Run the conversation agent
            text = device_action_task.input_text
            _LOGGER.debug("Prompt: %s", text)
            response = await agent.async_process(hass, text)
            await hass.async_block_till_done()
            _LOGGER.debug("Response: %s", response)

            if (traces := trace.async_get_traces()) and (last_trace := traces[-1]):
                context.conversation_trace = last_trace.as_dict()

            eval_record_writer.write(
                {
                    "uuid": str(uuid.uuid4()),  # Unique based on the model evaluated
                    "task_id": device_action_task.task_id,
                    "task": dataclasses.asdict(device_action_task),
                    "response": response,
                    "context": dataclasses.asdict(context),
                }
            )
