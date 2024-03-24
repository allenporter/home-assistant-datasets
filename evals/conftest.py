"""Test fixtures for evaluations."""

from collections.abc import Generator
import logging
import os
import pathlib
from slugify import slugify
from typing import Any
from unittest.mock import patch, mock_open

import pytest
import pytest_socket
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import area_registry as ar
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from home_assistant_datasets import secrets


_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None, None, None]:
    """Enable custom integration."""
    _ = enable_custom_integrations  # unused
    yield


@pytest.fixture(autouse=True)
async def mock_default_components(hass: HomeAssistant) -> None:
    """Fixture to setup required default components."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})


@pytest.fixture(autouse=True)
async def mock_synthetic_home(hass: HomeAssistant, synthetic_home_yaml: str) -> MockConfigEntry:
    """Fixture for mock configuration entry."""
    config_entry = MockConfigEntry(domain="synthetic_home", data={"config_filename": "ignored"})
    config_entry.add_to_hass(hass)


    with patch(
        "custom_components.synthetic_home.home_model.synthetic_home.read_config_content",
        mock_open(read_data=synthetic_home_yaml),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        assert config_entry.state == ConfigEntryState.LOADED
        yield



@pytest.fixture(name="synthetic_home_yaml")
def mock_synthetic_home_content(synthetic_home_config: str) -> str:
    """Mock out the yaml config file contents."""
    with pathlib.Path(synthetic_home_config).absolute().open("r") as f:
        return f.read()
    return ""



DEFAULT_OPENAI_PROMPT = """This smart home is controlled by Home Assistant.

An overview of the areas and the devices in this smart home:
{%- for area in areas() %}
{%- set area_info = namespace(printed=false) %}
{%- for device in area_devices(area) -%}
{%- if not device_attr(device, "disabled_by") and not device_attr(device, "entry_type") and device_attr(device, "name") %}
{%- if not area_info.printed %}
{{ area_name(area) }}:
{%- set area_info.printed = true %}
{%- endif %}
- {{ device_attr(device, "name") }}{% if device_attr(device, "model") and (device_attr(device, "model") | string) not in (device_attr(device, "name") | string) %} ({{ device_attr(device, "model") }}){% endif %}
{%- endif %}
{%- endfor %}
{%- endfor %}
Answer the user's questions about the world truthfully.
"""

@pytest.fixture(name="openai_config_entry")
async def mock_openai_conversation(hass: HomeAssistant) -> MockConfigEntry:
    config_entry = MockConfigEntry(
        domain="openai_conversation",
        data={
            "api_key": secrets.get_secret("api_key"),
        },
        options={
            "prompt": DEFAULT_OPENAI_PROMPT,
            "chat_model": "gpt-3.5-turbo",
            "max_tokens": 150,
            "top_p": 1.0,
            "temperature": 0.5,
        },
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state == ConfigEntryState.LOADED
    return config_entry


class ConversationAgent:
    """A client library for a conversation agent service call."""

    def __init__(self, agent_id: str) -> None:
        """Initialize the agent."""
        self._agent_id = agent_id

    async def async_process(self, hass: HomeAssistant, text: str) -> str:
        """Process a text input and return the response."""
        service_response = await hass.services.async_call(
            "conversation",
            "process",
            {"agent_id": self._agent_id, "text": text},
            blocking=True,
            return_response=True,
        )
        response = service_response["response"]
        return response["speech"]["plain"]["speech"]


@pytest.fixture(name="agent")
async def mock_agent(conversation_agent_id: str) -> ConversationAgent:
    """Create the conversation agent client id."""
    return ConversationAgent(conversation_agent_id)



class EvalRecordWriter:
    """Writes records to the eval output."""

    def __init__(self, eval_dir: str, filename: str):
        """Initialize EvalRecordWriter."""
        os.makedirs(eval_dir, exist_ok=True)
        self._eval_output = pathlib.Path(eval_dir) / filename
        self._fd = None

    async def open(self) -> None:
        """Initialize the record writer."""
        self._fd = open(self._eval_output, "w")
        self._records = 0


    async def write(self, record: dict[str, Any]) -> None:
        """Write an eval record."""
        self._fd.write(yaml.dump(record, sort_keys=False, explicit_start=True))
        self._records += 1

    async def close(self) -> None:
        """Close the evaluation record."""
        _LOGGER.info(
            "Wrote %s summariies to %s",
            self._records,
            self._eval_output,
        )

        if self._fd is None:
            self._fd.close()
            self._fd = None
