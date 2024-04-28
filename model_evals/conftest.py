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

from .common import ModelConfig, Models


_LOGGER = logging.getLogger(__name__)

MODEL_CONFIG_FILE = pathlib.Path("models.yaml")


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


@pytest.fixture
async def model_config(model_id: str) -> ModelConfig:
    """Fixture to read the model config yaml."""

    with MODEL_CONFIG_FILE.open() as fd:
        model_data = yaml.load(fd.read(), Loader=yaml.SafeLoader)

    models = model_data.get("models", [])
    for model in models:
        if (config := ModelConfig(**model)).model_id == model_id:
            return config

    raise ValueError(f"Model config file '{MODEL_CONFIG_FILE}' did not contain model_id: {model_id}")


@pytest.fixture(name="conversation_agent_config_entry")
async def mock_conversation_agent_config_entry(
    hass: HomeAssistant,
    model_config: ModelConfig,
    system_prompt: str | None
) -> MockConfigEntry:
    config_entry = MockConfigEntry(
        domain=model_config.domain,
        data=model_config.config_entry_data,
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
