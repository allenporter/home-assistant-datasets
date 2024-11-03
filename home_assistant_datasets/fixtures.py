"""Test fixtures for evaluations."""

from collections.abc import AsyncGenerator, Generator
import logging
import os
import pathlib
from typing import Any, TextIO, cast
from unittest.mock import patch, mock_open

import pytest
import pytest_socket
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
from homeassistant.setup import async_setup_component

from custom_components import synthetic_home  # noqa: F401

# TODO(#12): Support loading from the custom component or core development environment
from pytest_homeassistant_custom_component.common import MockConfigEntry

from home_assistant_datasets.data_model import ModelConfig

from . import data_model


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


@pytest.fixture(name="synthetic_home_config")
def mock_synthetic_home_config() -> str | None:
    """Fixture to load the synthetic home config."""
    return None


@pytest.fixture(name="synthetic_home_yaml")
def mock_synthetic_home_content(synthetic_home_config: str | None) -> str | None:
    """Mock out the yaml config file contents."""
    if synthetic_home_config is None:
        return None
    with pathlib.Path(synthetic_home_config).absolute().open("r") as f:
        return f.read()


@pytest.fixture(autouse=True, name="synthetic_home_config_entry")
async def mock_synthetic_home(
    hass: HomeAssistant, synthetic_home_yaml: str | None
) -> AsyncGenerator[MockConfigEntry | None, None]:
    """Fixture for mock configuration entry."""
    if synthetic_home_yaml is None:
        yield None
        return

    config_entry = MockConfigEntry(
        domain="synthetic_home", data={"config_filename": "ignored"}
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "synthetic_home.inventory.read_config_content",
            mock_open(read_data=synthetic_home_yaml),
        ),
        # Performance improvements during evaluation
        patch("custom_components.synthetic_home.cover.COVER_INSTANT", True),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        assert config_entry.state == ConfigEntryState.LOADED
        yield config_entry


@pytest.fixture(name="system_prompt")
async def system_prompt_fixture() -> None:
    """Fixture to provide the system prompt or None to use the default."""
    return None


@pytest.fixture
async def model_config(model_id: str) -> ModelConfig:
    """Fixture to read the model config yaml."""
    try:
        return data_model.read_model(model_id)
    except Exception as err:
        pytest.exit(str(err))


@pytest.fixture(name="conversation_agent_config_entry")
async def mock_conversation_agent_config_entry(
    hass: HomeAssistant, model_config: ModelConfig, system_prompt: str | None
) -> MockConfigEntry | None:
    if model_config.domain == "homeassistant":
        return None
    options = {}
    if model_config.config_entry_options:
        options.update(model_config.config_entry_options)
    if system_prompt:
        options["prompt"] = system_prompt
    config_entry = MockConfigEntry(
        domain=model_config.domain,
        data=model_config.config_entry_data,
        options=options,
        version=model_config.version or 1,
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
        assert service_response
        response = service_response["response"]
        return str(response["speech"]["plain"]["speech"])  # type: ignore[call-overload, index]


@pytest.fixture(name="conversation_agent_id")
async def mock_conversation_agent_id(
    model_config: ModelConfig,
    conversation_agent_config_entry: MockConfigEntry,
) -> str:
    """Return the id for the conversation agent under test."""
    if model_config.domain == "homeassistant":
        return "conversation.home_assistant"
    return "conversation.mock_title"  # conversation_agent_config_entry.entry_id)


@pytest.fixture(name="agent")
async def mock_agent(conversation_agent_id: str) -> ConversationAgent:
    """Create the conversation agent client id."""
    return ConversationAgent(conversation_agent_id)


class EvalRecordWriter:
    """Writes records to the eval output."""

    def __init__(self, filename: pathlib.Path):
        """Initialize EvalRecordWriter."""
        os.makedirs(filename.parent, exist_ok=True)
        self._eval_output = filename
        self._fd: TextIO | None = None

    def open(self) -> None:
        """Initialize the record writer."""
        self._fd = open(self._eval_output, "w")
        self._records = 0

    def write(self, record: dict[str, Any]) -> None:
        """Write an eval record."""
        assert self._fd
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


@pytest.fixture(name="eval_record_writer")
def eval_record_writer_fixture(
    hass: HomeAssistant,
    eval_output_file: pathlib.Path,
) -> Generator[EvalRecordWriter, None, None]:
    """Fixture that prepares the eval output writer."""
    writer = EvalRecordWriter(eval_output_file)
    writer.open()
    yield writer
    writer.close()


@pytest.fixture(autouse=True)
def validate_entities(
    hass: HomeAssistant,
    synthetic_home_config_entry: MockConfigEntry,
    synthetic_home_yaml: str,
) -> None:
    """Fixture to verify that all entities are property created by synthetic home to avoid misconfiguration."""
    inventory = yaml.load(synthetic_home_yaml, Loader=yaml.Loader)
    assert inventory
    if not (entities := inventory.get("entities")):
        raise ValueError(
            f"No entities were specified in the inventory file: {inventory.keys()}"
        )
    for entity in entities:
        entity_id = entity["id"]
        state = hass.states.get(entity_id)
        assert state, f"Entity id not created {entity_id}"
        assert state.state != "unavailable"
        assert state.state not in (
            "unavailable",
            "unknown",
        ), f"Entity id has unavailable state {entity_id}: {state.state}"
