"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

from collections.abc import Generator, Callable, Awaitable
import logging
import pathlib
from typing import Any
import uuid
from slugify import slugify
import dataclasses
from unittest.mock import patch

import pytest
from pytest_subtests import SubTests
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er, device_registry as dr

from .conftest import ConversationAgent, EvalRecordWriter
from .common import SyntheticDeviceState, HomeAssistantContext, ModelConfig


_LOGGER = logging.getLogger(__name__)

MODEL_EVAL_OUTPUT = "model_outputs/device_actions"



@pytest.fixture(
    name="model_id",
    params=[
        "gemini-1.5-flash",
        # Have not tested with these models yet
        # "gpt-3.5",
        # "gemma",
        # "mistral-7b-instruct",
    ],
)
def model_id_fixture(request: pytest.FixtureRequest) -> str:
    """Fiture that defines which model is being evaluated."""
    return request.param


@pytest.fixture(name="eval_record_writer")
def eval_record_writer_fixture(
    hass: HomeAssistant,
    model_config: ModelConfig,
    synthetic_home_config: str
) -> Generator[EvalRecordWriter, None, None]:
    """Fixture that prepares the eval output writer."""
    writer = EvalRecordWriter(
        pathlib.Path(MODEL_EVAL_OUTPUT) / model_config.model_id,
        pathlib.Path(synthetic_home_config).name,
    )
    writer.open()
    yield writer
    writer.close()


@dataclasses.dataclass
class DeviceActionTask:
    """Detail about the task that is being evaluated."""

    home_id: str
    """Identifier for the synethetic home."""

    area_name: str
    """Area name that contains the specified device."""

    input_text: str
    """The conversation input text to state."""

    device_state: SyntheticDeviceState
    """The device state details  about the state of the devices under evaluation"""

    @property
    def task_id(self) -> str:
        """An identifier that labels this area summary evaluation task."""
        return f"{self.home_id}-{slugify(self.device_state.device_name)}-{self.device_state.state_label}-{self.input_text}"



@pytest.fixture(name="tasks_provider")
def tasks_provider_fixture(
    hass: HomeAssistant,
    synthetic_home_yaml: str
) -> Callable[[], Generator[DeviceActionTask, None, None]]:
    """Fixture that generates the tasks to evaluate."""

    synthetic_home_config = yaml.load(synthetic_home_yaml, Loader=yaml.Loader)
    home_name = synthetic_home_config["name"]
    home_id = slugify(home_name)

    def func() -> Generator[DeviceActionTask, None, None]:
        yield DeviceActionTask(
            home_id=home_id,
            area_name="Bedroom 3",
            input_text="Please turn on the bedroom 3 light",
            device_state=SyntheticDeviceState(
                device_name="Bedroom 3 Light",
                restorable_attribute="off",
            ),
        )

    return func


@pytest.fixture(name="prompt_context_recorder", autouse=True)
def mock_record_prompt_contex_fixturet() -> None:
    """A fixture to record generative model prompts."""

    # def side_effect(*args, **kwargs):
    #     _LOGGER.info("side_effect called arg:  %s", args)
    #     _LOGGER.info("side_effect called kw:  %s", kwargs)

    # with patch("homeassistant.components.google_generative_ai_conversation.conversation.genai.GenerativeModel.start_chat", side_effect=side_effect) as mock_model:
    #     yield



def get_device_eval_context(hass: HomeAssistant, device_entry: dr.DeviceEntry) -> dict[str, Any]:
    """Return information about a device used for dumping a context record."""
    detail = {}
    # Dump device information
    if device_entry.model:
        detail["model"] = device_entry.model
    if device_entry.manufacturer:
        detail["manufacturer"] = device_entry.manufacturer
    # Dump entity information
    entity_registry = er.async_get(hass)
    for entity_entry in er.async_entries_for_device(entity_registry, device_entry.id):
        if state := hass.states.get(entity_entry.entity_id):
            state_str = state.state
            if uom := state.attributes.get("unit_of_measurement"):
                state_str = f"{state_str} {uom}"
            detail[entity_entry.entity_id] = state_str
    return detail


@pytest.fixture(name="prepare_state")
async def prepare_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> Callable[[DeviceActionTask], Awaitable[None]]:
    """Fixture with a function call to change device state for evaluation."""

    async def func(task: DeviceActionTask) -> None:
        device_state = task.device_state
        _LOGGER.info("Changing device state for %s to %s", device_state.device_name, device_state.restorable_attribute)
        await hass.services.async_call(
            "synthetic_home",
            "set_synthetic_device_state",
            service_data={
                "config_entry_id": synthetic_home_config_entry.entry_id,
                "area": task.area_name,
                "device": device_state.device_name,
                "device_state_key": device_state.restorable_attribute,
            },
            blocking=True,
        )

        return HomeAssistantContext(device_context={})

    return func


@pytest.mark.parametrize(
    ("synthetic_home_config"),
    [
        ("datasets/devices/apartament4-pl.yaml"),
    ],
)
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
