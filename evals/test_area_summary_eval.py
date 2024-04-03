"""An evaluation for an Area Summary agent."""

from collections.abc import Generator, Callable, Awaitable
import logging
import pathlib
from typing import Any
import uuid

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


@pytest.fixture(name="conversation_agent_id")
async def mock_conversation_agent_id(
    conversation_agent_domain: str,
    openai_config_entry: MockConfigEntry,
    vicuna_conversation_config_entry: MockConfigEntry,
) -> str:
    """Return the id for the conversation agent under test."""
    if conversation_agent_domain == "openai_conversation":
        return openai_config_entry.entry_id
    if conversation_agent_domain == "vicuna_conversation":
        return vicuna_conversation_config_entry.entry_id
    raise ValueError(f"Conversation Agent domain not found: {conversation_agent_domain}")


@pytest.fixture(name="eval_record_writer")
def eval_record_writer_fixture(hass: HomeAssistant, model_id: str, synthetic_home_config: str) -> Generator[EvalRecordWriter, None, None]:
    """Fixture that prepares the eval output writer."""
    writer = EvalRecordWriter(
        pathlib.Path("out") / model_id,
        pathlib.Path(synthetic_home_config).name,
    )
    writer.open()
    yield writer
    writer.close()


def get_device_eval_context(hass: HomeAssistant, device_entry: dr.DeviceEntry) -> dict[str, Any]:
    """Return information about a device used for dumping a context record."""
    detail = {}
    # Device information
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


def get_device_context_for_area(hass: HomeAssistant, area_id: str) -> dict[str, str]:
    """Return the current entity states for an aarea."""
    device_registry = dr.async_get(hass)
    return {
        device_entry.name: get_device_eval_context(hass, device_entry)
        for device_entry in dr.async_entries_for_area(device_registry, area_id)
    }


@pytest.fixture(name="device_restorable_states")
def device_restorable_states_fixture(synthetic_home_yaml: str) -> Callable[[str], Generator[list[tuple[str, str]], None, None]]:
    """Fixture that prepares the device states that need to be evaluated."""

    synthetic_home_config = yaml.load(synthetic_home_yaml, Loader=yaml.Loader)

    def func(area_name: str) -> Generator[tuple[str | None, str | None], None, None]:
        if (devices := synthetic_home_config["devices"].get(area_name)) is None:
            return
        for device_info in devices:
            attributes = load_restorable_attributes(device_info["device_type"])
            for attribute in attributes:
                yield device_info["name"], attribute

    return func


@pytest.fixture(name="set_synthetic_device_state")
async def set_synthetic_device_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry
) -> Callable[[str, str, str], Awaitable[None]]:
    """Fixture with a function call to change device state for evaluation."""

    async def func(area_name: str, device_name: str, restorable_attribute: str) -> None:
        _LOGGER.info("Changing device state for %s to %s", device_name, restorable_attribute)
        await hass.services.async_call(
            "synthetic_home",
            "set_synthetic_device_state",
            service_data={
                "config_entry_id": synthetic_home_config_entry.entry_id,
                "area": area_name,
                "device": device_name,
                "restorable_attribute_key": restorable_attribute,
            },
            blocking=True,
        )

    return func


@pytest.mark.parametrize(
    ("model_id", "conversation_agent_domain", "system_prompt"),
    [
        # model_id is unique path output identifying this model
        ("gpt-3.5", "openai_conversation", AREA_SUMMARY_PROMPT),
        ("mistral-7b-instruct", "vicuna_conversation", AREA_SUMMARY_PROMPT),
    ],
    ids=["mistral-7b-instruct", "gpt-3.5"]
)
@pytest.mark.parametrize(
    ("synthetic_home_config"),
    [
        ("datasets/devices/home1-us.yaml"),
        ("datasets/devices/apartament4-pl.yaml"),
        ("datasets/devices/casa-adosada-en-la-costa-es.yaml"),
        ("datasets/devices/lakeside-retreat-de.yaml"),
    ],
)
async def test_areas(
    hass: HomeAssistant,
    agent: ConversationAgent,
    eval_record_writer: EvalRecordWriter,
    subtests: SubTests,
    device_restorable_states: Generator[tuple[str | None, str | None], None, None],
    set_synthetic_device_state: Callable[[str, str, str], Awaitable[None]],
) -> None:
    """Evaluation that tests an area summary."""

    area_registry = ar.async_get(hass)
    area_entries = list(area_registry.async_list_areas())
    _LOGGER.info("Loaded %s areas to evaluate", len(area_entries))

    i = 0
    for area_entry in area_entries:
        area_name = area_entry.name
        for device_name, restorable_attribute in device_restorable_states(area_name):
            with subtests.test(msg=f"{area_name}-{device_name}-{restorable_attribute}", i=i):
                i = i + 1

                 # Exercice a different state of the device
                _LOGGER.info("Changing device state for %s to %s", device_name, restorable_attribute)
                await set_synthetic_device_state(area_name, device_name, restorable_attribute)

                _LOGGER.info(
                    "Evaluating area summary: %s",
                    area_name,
                )
                prompt = make_prompt(area_name)
                _LOGGER.debug("Evaluating prompt: %s", prompt)
                response = await agent.async_process(hass, prompt)
                _LOGGER.debug("Response: %s", response)
                response = cleanup_response(response)

                eval_record_writer.write(
                    {
                        "task": f"{area_name}-{device_name}-{restorable_attribute}"
                        "uuid": str(uuid.uuid4()),
                        "area": area_name,
                        "response": response,
                        "device_detail": get_device_context_for_area(hass, area_entry.id),
                    }
                )
