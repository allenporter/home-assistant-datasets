"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

from dataclasses import dataclass
from collections.abc import Generator, Callable, Awaitable
import logging
import pathlib
import uuid
from slugify import slugify
import dataclasses

import pytest
from pytest_subtests import SubTests
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr

from .conftest import ConversationAgent, EvalRecordWriter
from .common import HomeAssistantContext


_LOGGER = logging.getLogger(__name__)

MODEL_EVAL_OUTPUT = "model_outputs/device_actions"


@pytest.fixture(name="eval_output_dir")
def eval_output_dir_fixture() -> str:
    return MODEL_EVAL_OUTPUT


@pytest.fixture(
    name="model_id",
    params=[
        "gemini-1.5-flash",
        "gpt-4o",
        # "mistral-7b-instruct",
    ],
)
def model_id_fixture(request: pytest.FixtureRequest) -> str:
    """Fiture that defines which model is being evaluated."""
    return request.param


@pytest.fixture(
    name="synthetic_home_config",
    params=[
        "datasets/devices/desert-retreat-us.yaml",
        "datasets/devices/dom1-pl.yaml",
        "datasets/devices/home1-us.yaml",
        "datasets/devices/home7-dk.yaml",
    ],
)
def synthetic_home_config_fixture(request: pytest.FixtureRequest) -> str:
    """Fiture that defines the synthetic home configuration to use."""
    return request.param


@pytest.fixture(name="device_actions_config")
def device_actions_config_fixture(synthetic_home_config: str) -> str:
    """Fixture with the specific tasks to evaluate."""
    home_file = pathlib.Path(synthetic_home_config).name
    return f"datasets/device-actions/{home_file}"


@dataclass
class SyntheticDeviceState:
    """Information needed to set the synthetic state for an evaluation task."""

    name: str
    area: str
    state: str

    @property
    def state_label(self) -> str:
        """Identifier about the state of the devices under evaluation"""
        return f"{slugify(self.name)}-{slugify(self.area)}-{slugify(self.state)}"


@dataclasses.dataclass
class DeviceActionTask:
    """Detail about the task that is being evaluated."""

    home_id: str
    """Identifier for the synethetic home."""

    input_text: str
    """The conversation input text to state."""

    device_states: SyntheticDeviceState
    """The device state details  about the state of the devices under evaluation"""

    @property
    def task_id(self) -> str:
        """An identifier that labels this area summary evaluation task."""
        return f"{self.home_id}-{[s.state_label for s in self.device_states]}-{self.input_text}"


@pytest.fixture(name="tasks_provider")
def tasks_provider_fixture(
    hass: HomeAssistant,
    device_actions_config: str,
) -> Callable[[], Generator[DeviceActionTask, None, None]]:
    """Fixture that generates the tasks to evaluate."""

    device_actions_file = pathlib.Path(device_actions_config)
    docs = yaml.load_all(device_actions_file.read_text(), Loader=yaml.SafeLoader)

    def func() -> Generator[DeviceActionTask, None, None]:
        for doc in docs:
            home_id = doc["home"]
            for action in doc["actions"]:
                sentences = action["sentences"]

                device_states = [
                    SyntheticDeviceState(**device_state)
                    for device_state in action["device_states"]
                ]
                assert isinstance(device_states, list)

                for sentence in sentences:
                    yield DeviceActionTask(
                        home_id=home_id,
                        input_text=sentence,
                        device_states=device_states,
                    )

    return func


@pytest.fixture(name="prepare_state")
async def prepare_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> Callable[[DeviceActionTask], Awaitable[HomeAssistantContext]]:
    """Fixture with a function call to change device state for evaluation."""

    async def func(task: DeviceActionTask) -> HomeAssistantContext:
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

        return HomeAssistantContext()

    return func


@pytest.mark.parametrize("expected_lingering_timers", [(True)])
async def test_collect_device_actions(
    hass: HomeAssistant,
    agent: ConversationAgent,
    eval_record_writer: EvalRecordWriter,
    subtests: SubTests,
    tasks_provider: Callable[[], Generator[DeviceActionTask, None, None]],
    prepare_state: Callable[[DeviceActionTask], Awaitable[HomeAssistantContext]],
) -> None:
    """Collects model responses for area summaries."""

    for i, device_action_task in enumerate(tasks_provider()):
        with subtests.test(msg=device_action_task.task_id, i=i):

            # Setup the home for evaluation
            context = await prepare_state(device_action_task)

            # Run the conversation agent
            text = device_action_task.input_text
            _LOGGER.debug("Prompt: %s", text)
            response = await agent.async_process(hass, text)
            _LOGGER.debug("Response: %s", response)

            eval_record_writer.write(
                {
                    "uuid": str(uuid.uuid4()),  # Unique based on the model evaluated
                    "task_id": device_action_task.task_id,
                    "task": dataclasses.asdict(device_action_task),
                    "response": response,
                    "context": dataclasses.asdict(context),
                }
            )
