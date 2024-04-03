"""Test fixtures for evaluations."""

from collections.abc import Generator
import logging
import os
import pathlib
from typing import Any, TextIO
from unittest.mock import patch, mock_open

import pytest
import pytest_socket
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from home_assistant_datasets import secrets

from custom_components import synthetic_home  # noqa: F401


_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def mock_allow_sockets(socket_enabled: Any) -> None:
    """Remove all restrictions talking to sockets.

    This is needed when talking to external data sources
    like LLMs.
    """
    pytest_socket.pytest_runtest_teardown()
    pass


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


@pytest.fixture(autouse=True, name="synthetic_home_config_entry")
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
        yield config_entry


@pytest.fixture(name="synthetic_home_yaml")
def mock_synthetic_home_content(synthetic_home_config: str) -> str:
    """Mock out the yaml config file contents."""
    with pathlib.Path(synthetic_home_config).absolute().open("r") as f:
        return f.read()
    return ""


@pytest.fixture(name="system_prompt")
async def system_prompt_fixture() -> None:
    """Fixture to provide the system prompt or None to use the default."""
    return None



@pytest.fixture(name="openai_config_entry")
async def mock_openai_conversation(hass: HomeAssistant, system_prompt: str | None) -> MockConfigEntry:
    config_entry = MockConfigEntry(
        domain="openai_conversation",
        data={
            "api_key": secrets.get_secret("openai_api_key"),
        },
        options={"prompt": system_prompt} if system_prompt else {},
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state == ConfigEntryState.LOADED
    return config_entry



@pytest.fixture(name="google_genai_config_entry")
async def mock_google_generative_ai_conversation(hass: HomeAssistant, system_prompt: str | None) -> MockConfigEntry:
    config_entry = MockConfigEntry(
        domain="google_generative_ai_conversation",
        data={
            "api_key": secrets.get_secret("google_api_key"),
        },
        options={"prompt": system_prompt} if system_prompt else {},
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state == ConfigEntryState.LOADED
    return config_entry


@pytest.fixture(name="vicuna_conversation_config_entry")
async def mock_vicuna_conversation(hass: HomeAssistant, system_prompt: str) -> MockConfigEntry:
    # Ensure custom components used in the test are loaded
    from custom_components import vicuna_conversation  # noqa: F401

    config_entry = MockConfigEntry(
        domain="vicuna_conversation",
        data={
            "api_key": "sk-0000000000000000000",
            "base_url": secrets.get_secret("vicuna_convesation_base_url"),
        },
        options={"prompt": system_prompt} if system_prompt else {},
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

    def __init__(self, eval_dir: pathlib.Path, filename: str):
        """Initialize EvalRecordWriter."""
        os.makedirs(eval_dir, exist_ok=True)
        self._eval_output = eval_dir / filename
        self._fd: TextIO | None = None

    def open(self) -> None:
        """Initialize the record writer."""
        self._fd = open(self._eval_output, "w")
        self._records = 0

    def write(self, record: dict[str, Any]) -> None:
        """Write an eval record."""
        self._fd.write(yaml.dump(record, sort_keys=False, explicit_start=True))
        self._fd.flush()
        self._records += 1

    def close(self) -> None:
        """Close the evaluation record."""
        _LOGGER.info(
            "Wrote %s summariies to %s",
            self._records,
            self._eval_output,
        )

        if self._fd is not None:
            self._fd.close()
            self._fd = None
