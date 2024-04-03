"""An evaluation for an Area Summary agent."""

from collections.abc import Generator, Callable, Awaitable
import logging
import pathlib
from typing import Any
import uuid
from slugify import slugify
import dataclasses
from dataclasses import dataclass

import pytest
from pytest_subtests import SubTests
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import area_registry as ar, entity_registry as er, device_registry as dr

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.synthetic_home.home_model.device_types import load_restorable_attributes

from .conftest import ConversationAgent, EvalRecordWriter


_LOGGER = logging.getLogger(__name__)


AREA_SUMMARY_PROMPT = """
Please summarize the status of an area of the home. Your summaries are succint,
and do not mention boring details or things that seem very mundane or minor. A
one sentence summary is best.

Here is an example of the input and output:

Area: Bedroom 1
- Bedroom 1 Light (Dimmable Smart Bulb)
    light: off
- Smart Lock (Encode Smart WiFi Deadbolt)
    binary_sensor: off
    binary_sensor Tamper: off
    binary_sensor Battery: off
    sensor Battery: 90 %
Summary: The bedroom is secure.

Area: Driveway
- Black Model 3 (Model 3)
  - binary_sensor Charging: off
  - sensor Battery level: 90%
  - sensor Battery range: 200 mi
  - binary_sensor Pedestrian Gate: off
  - switch Sprinkler: off
Summary: The car is almost charged.

Here is the current state of all Areas. The user will ask you about one of these:

{%- for area in areas() %}
Area: {{ area }}
  {%- for device in area_devices(area) -%}
    {%- if not device_attr(device, "disabled_by") and not device_attr(device, "entry_type") and device_attr(device, "name") %}
        {%- set device_name = device_attr(device, "name_by_user") | default(device_attr(device, "name"), True) %}

- {{ device_name  }}{% if device_attr(device, "model") and (device_attr(device, "model") | string) not in (device_attr(device, "name") | string) %} ({{ device_attr(device, "model") }}){% endif %}
      {%- set entity_info = namespace(printed=false) %}
      {%- for entity_id in device_entities(device) -%}
        {%- set entity_name = state_attr(entity_id, "friendly_name") | replace(device_name, "") | trim %}
    {{ entity_id.split(".")[0] -}}
        {%- if entity_name %} {{ entity_name }}{% endif -%}
        : {{ states(entity_id, rounded=True, with_unit=True) }}
      {%- endfor %}
    {%- endif %}
  {%- endfor %}
{%- endfor %}
"""

AREA_PROMPT = """
Area: {area_name}
Summary:
"""

STRIP_PREFIX = "Summary: "


@dataclass
class SyntheticDeviceState:
    """Information needed to set the synthetic state for an evaluation task."""

    device_name: str
    restorable_attribute: str

    @property
    def state_label(self) -> str:
        """Identifier about the state of the devices under evaluation"""
        return f"{slugify(self.device_name)}-{slugify(self.restorable_attribute)}"


@dataclass
class AreaSummaryTask:
    """Detail about the task that is being evaluated."""

    home_id: str
    """Identifier for the synethetic home."""

    home_name: str
    """Human readable name for the home for context."""

    area_id: str
    """Identifier for the area being summarized."""

    area_name: str
    """Area name within the home that is being summarized and evaluated."""

    device_state: SyntheticDeviceState
    """The device state details  about the state of the devices under evaluation"""

    @property
    def task_id(self) -> str:
        """An identifier that labels this area summary evaluation task."""
        return f"{self.home_id}-{slugify(self.area_name)}-{self.device_state.state_label}"


@dataclass
class HomeAssistantContext:
    """Additional context about the actual state of Home Assistant that si being evaluated."""

    device_context: dict[str, Any]
    """Details that reflect the actual synthetic device states under evaluation."""


@dataclass
class ModelConfig:
    """The configuration for the conversation agent under evaluation."""

    conversation_agent_domain: str
    """The domain under evaluation."""

    model_id: str
    """Details about the model name being evaluated if the domain supports multiple models."""



@pytest.fixture(name="system_prompt")
def system_prompt_fixture() -> str:
    return AREA_SUMMARY_PROMPT


def make_prompt(area_name: str) -> str:
    """Create a prompt for the agent to summarize the area."""
    return AREA_PROMPT.format(
        area_name=area_name,
    )


def cleanup_response(response: str) -> str:
    """Perform any cleanup on the response where the LLM returns part of the prompt."""
    response = response.lstrip()
    try:
        index = response.index(STRIP_PREFIX)
    except ValueError:
        return response
    return response[index+len(STRIP_PREFIX):]


@pytest.fixture(
    name="model_config",
    params=[
        (ModelConfig("google_generative_ai_conversation", "gemini-pro")),
        (ModelConfig("openai_conversation", "gpt-3.5")),
        (ModelConfig("vicuna_conversation", "mistral-7b-instruct")),
    ],
)
def model_config_fixture(request: pytest.FixtureRequest) -> ModelConfig:
    """Fiture that defines which model is being evaluated."""
    return request.param


@pytest.fixture(name="conversation_agent_id")
async def mock_conversation_agent_id(
    model_config: ModelConfig,
    openai_config_entry: MockConfigEntry,
    vicuna_conversation_config_entry: MockConfigEntry,
    google_genai_config_entry: MockConfigEntry,
) -> str:
    """Return the id for the conversation agent under test."""
    if model_config.conversation_agent_domain == "openai_conversation":
        return openai_config_entry.entry_id
    if model_config.conversation_agent_domain == "google_generative_ai_conversation":
        return google_genai_config_entry.entry_id
    if model_config.conversation_agent_domain == "vicuna_conversation":
        return vicuna_conversation_config_entry.entry_id
    raise ValueError(f"Conversation Agent domain not found: {model_config.conversation_agent_domain}")


@pytest.fixture(name="eval_record_writer")
def eval_record_writer_fixture(
    hass: HomeAssistant,
    model_config: ModelConfig,
    synthetic_home_config: str
) -> Generator[EvalRecordWriter, None, None]:
    """Fixture that prepares the eval output writer."""
    writer = EvalRecordWriter(
        pathlib.Path("out") / model_config.model_id,
        pathlib.Path(synthetic_home_config).name,
    )
    writer.open()
    yield writer
    writer.close()


@pytest.fixture(name="tasks_provider")
def tasks_provider_fixture(
    hass: HomeAssistant,
    synthetic_home_yaml: str
) -> Callable[[], Generator[AreaSummaryTask, None, None]]:
    """Fixture that generates the tasks to evaluate."""

    synthetic_home_config = yaml.load(synthetic_home_yaml, Loader=yaml.Loader)
    home_name = synthetic_home_config["name"]
    home_id = slugify(home_name)

    area_registry = ar.async_get(hass)
    area_entries = list(area_registry.async_list_areas())
    _LOGGER.info("Loaded %s areas to evaluate", len(area_entries))

    def func() -> Generator[AreaSummaryTask, None, None]:
        for area_entry in area_entries:
            area_name = area_entry.name

            if (devices := synthetic_home_config["devices"].get(area_name)) is None:
                return
            for device_info in devices:
                attributes = load_restorable_attributes(device_info["device_type"])
                for attribute in attributes:
                    device_state = SyntheticDeviceState(device_info["name"], attribute)

                    yield AreaSummaryTask(
                        home_id=home_id,
                        home_name=home_name,
                        area_id=area_entry.id,
                        area_name=area_name,
                        device_state=device_state,
                    )

    return func


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
    synthetic_home_config_entry: ConfigEntry
) -> Callable[[AreaSummaryTask], Awaitable[None]]:
    """Fixture with a function call to change device state for evaluation."""

    async def func(area_summary_task: AreaSummaryTask) -> None:
        device_state = area_summary_task.device_state
        _LOGGER.info("Changing device state for %s to %s", device_state.device_name, device_state.restorable_attribute)
        await hass.services.async_call(
            "synthetic_home",
            "set_synthetic_device_state",
            service_data={
                "config_entry_id": synthetic_home_config_entry.entry_id,
                "area": area_summary_task.area_name,
                "device": device_state.device_name,
                "restorable_attribute_key": device_state.restorable_attribute,
            },
            blocking=True,
        )

        device_registry = dr.async_get(hass)
        return HomeAssistantContext(device_context={
            device_entry.name: get_device_eval_context(hass, device_entry)
            for device_entry in dr.async_entries_for_area(device_registry, area_id)
        })

    return func


@pytest.mark.parametrize(
    ("synthetic_home_config"),
    [
        ("datasets/devices/home1-us.yaml"),
        ("datasets/devices/apartament4-pl.yaml"),
        ("datasets/devices/casa-adosada-en-la-costa-es.yaml"),
        ("datasets/devices/lakeside-retreat-de.yaml"),
    ],
)
async def test_collect_area_summaries(
    hass: HomeAssistant,
    agent: ConversationAgent,
    eval_record_writer: EvalRecordWriter,
    subtests: SubTests,
    tasks_provider: Callable[[], Generator[AreaSummaryTask, None, None]],
    prepare_state: Callable[[AreaSummaryTask], Awaitable[HomeAssistantContext]],
) -> None:
    """Collects model responses for area summaries."""

    for i, area_summary_task in enumerate(tasks_provider()):
        with subtests.test(msg=area_summary_task.task_id, i=i):

            # Setup the home for evaluation
            context = await prepare_state(area_summary_task)

            # Run the conversation agent
            area_name = area_summary_task.area_name
            prompt = make_prompt(area_name)
            _LOGGER.info("Performing area summary: %s", area_name)
            _LOGGER.debug("Area summary prompt: %s", prompt)
            response = await agent.async_process(hass, prompt)
            _LOGGER.debug("Area summary response: %s", response)
            response = cleanup_response(response)

            eval_record_writer.write(
                {
                    "uuid": str(uuid.uuid4()),  # Unique based on the model evaluated
                    "task_id": area_summary_task.task_id,
                    "task": dataclasses.asdict(area_summary_task),
                    "response": response,
                    "context": dataclasses.asdict(context),
                }
            )
