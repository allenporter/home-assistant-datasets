"""Test fixtures for loading a conversation agent.

Tests should provide a `model_id` fixture that references a model in the
registry (either `models.yaml` or `models/` in a yaml file)
"""

import logging
from typing import Any

import pytest
import pytest_socket

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState, ConfigEntry
from homeassistant.setup import async_setup_component

from home_assistant_datasets.data_model import (
    ModelConfig,
    EntryConfig,
    DatasetCard,
    read_model,
)
from home_assistant_datasets.agent import (
    ConversationAgent,
    create_default_agent,
)

# TODO(#12): Support loading from the custom component or core development environment
from pytest_homeassistant_custom_component.common import MockConfigEntry


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
async def mock_default_components(hass: HomeAssistant) -> None:
    """Fixture to setup required default components."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})


@pytest.fixture(scope="module")
async def model_config(model_id: str) -> ModelConfig:
    """Fixture to read the model config yaml."""
    try:
        return read_model(model_id)
    except Exception as err:
        pytest.exit(str(err))


@pytest.fixture(name="system_prompt")
async def system_prompt_fixture() -> None:
    """Fixture to provide the system prompt or None to use the default."""
    return None


@pytest.fixture(name="conversation_agent_config_entry")
async def mock_conversation_agent_config_entry(
    hass: HomeAssistant,
    model_config: ModelConfig,
    system_prompt: str | None,
    prerequisites: list[EntryConfig],
    dataset_card: DatasetCard,
) -> MockConfigEntry | None:
    """Fixture to create a conversation agent config entry."""

    for entry in prerequisites:
        config_entry = MockConfigEntry(
            domain=entry.domain,
            data=entry.config_entry_data,
            options=entry.config_entry_options,
            version=entry.version or 1,
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        assert config_entry.state == ConfigEntryState.LOADED

    if model_config.domain == "homeassistant":
        return None
    options: dict[str, Any] = {}
    if model_config.config_entry_options:
        options.update(model_config.config_entry_options)
    data: dict[str, Any] = {}
    if model_config.config_entry_data:
        data.update({**model_config.config_entry_data})

    # Override any config entr data from the dataset (e.g. changing LLM API)
    if dataset_card.config_entry_options:
        options.update(dataset_card.config_entry_options)
    if dataset_card.config_entry_data:
        data.update(dataset_card.config_entry_data)

    if system_prompt:
        options["prompt"] = system_prompt
    config_entry = MockConfigEntry(
        domain=model_config.domain,
        data=data,
        options=options,
        version=model_config.version or 1,
    )
    _LOGGER.info("Config entry options=%s", config_entry.options)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state == ConfigEntryState.LOADED
    return config_entry


@pytest.fixture(name="conversation_agent_id", scope="module")
async def mock_conversation_agent_id(model_config: ModelConfig) -> str:
    """Return the id for the conversation agent under test."""
    if model_config.domain == "homeassistant":
        return "conversation.home_assistant"
    return "conversation.mock_title"


@pytest.fixture(name="rate_limited_agent", scope="module")
async def rate_limited_agent_fixture(
    conversation_agent_id: str,
    model_config: ModelConfig,
) -> ConversationAgent:
    """Create the conversation agent client id."""
    return create_default_agent(conversation_agent_id, model_config.rpm)


@pytest.fixture(name="agent")
async def agent_fixture(
    rate_limited_agent: ConversationAgent,
    conversation_agent_config_entry: ConfigEntry,
) -> ConversationAgent:
    """Fixture to ensure the conversation agent and config entry are loaded."""
    return rate_limited_agent
