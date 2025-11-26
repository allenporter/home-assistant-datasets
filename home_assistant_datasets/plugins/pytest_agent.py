"""Test fixtures for loading a conversation agent.

Tests should provide a `model_id` fixture that references a model in the
registry (either `models.yaml` or `models/` in a yaml file).

This also depends on the `pytest_dataset` plugin for loading any dataset
specific agent configuration needed.
"""

import dataclasses
import logging
from typing import Any

import pytest
import pytest_socket

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState, ConfigEntry
from homeassistant.setup import async_setup_component


from home_assistant_datasets.agent import (
    ConversationAgent,
    create_default_agent,
    create_ai_task_agent,
)
from home_assistant_datasets.datasets.dataset_card import (
    DatasetCard,
)
from home_assistant_datasets.models import (
    ModelConfig,
    read_model,
    read_prerequisites,
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


@pytest.fixture(scope="module")
def model_config(model_id: str) -> ModelConfig:
    """Fixture to read the model config yaml."""
    try:
        return read_model(model_id)
    except Exception as err:
        pytest.exit(str(err))


@pytest.fixture(name="system_prompt")
def system_prompt_fixture() -> None:
    """Fixture to provide the system prompt or None to use the default."""
    return None


@pytest.fixture(name="merged_model_config")
def merged_model_config_fixture(
    model_config: ModelConfig,
    dataset_card: DatasetCard,
    system_prompt: str | None,
) -> ModelConfig:
    """Fixture that merges in model settings from the DataSet card."""
    options: dict[str, Any] = {}
    if model_config.config_entry_options:
        options.update(model_config.config_entry_options)
    data: dict[str, Any] = {}
    if model_config.config_entry_data:
        data.update({**model_config.config_entry_data})

    # Override any config entry data from the dataset (e.g. changing LLM API)
    if dataset_card.config_entry_options:
        options.update(dataset_card.config_entry_options)
    if dataset_card.config_entry_data:
        data.update(dataset_card.config_entry_data)

    # Override the default system prompt with a fixture specific prompt
    if system_prompt:
        options["prompt"] = system_prompt

    return dataclasses.replace(
        model_config,
        config_entry_options=options,
        config_entry_data=data,
    )


@pytest.fixture(name="conversation_agent_config_entry")
async def mock_conversation_agent_config_entry(
    hass: HomeAssistant,
    merged_model_config: ModelConfig,
) -> MockConfigEntry | None:
    """Fixture to create a conversation agent config entry."""
    if merged_model_config.domain == "homeassistant":
        return None
    config_entry = MockConfigEntry(
        domain=merged_model_config.domain,
        data=merged_model_config.config_entry_data,
        options=merged_model_config.config_entry_options,
        version=merged_model_config.version or 1,
        minor_version=merged_model_config.minor_version or 0,
        subentries_data=merged_model_config.subentries_data,
    )
    _LOGGER.info("Config entry options=%s", config_entry.options)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state == ConfigEntryState.LOADED
    return config_entry


@pytest.fixture(name="conversation_agent_id", scope="module")
def mock_conversation_agent_id(model_config: ModelConfig) -> str:
    """Return the id for the conversation agent under test."""
    if model_config.domain == "homeassistant":
        return "conversation.home_assistant"
    return "conversation.mock_title"


@pytest.fixture(name="rate_limited_agent", scope="module")
def rate_limited_agent_fixture(
    conversation_agent_id: str,
    model_config: ModelConfig,
) -> ConversationAgent:
    """Create the conversation agent.

    This is a module level fixture to ensure the rate limit is respected across
    individual test runs.
    """
    return create_default_agent(conversation_agent_id, model_config.rpm)


@pytest.fixture(name="configure_prerequisites")
async def configure_prerequisites_fixture(hass: HomeAssistant) -> None:
    """Fixture to load prerequisite integrations."""

    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})
    assert await async_setup_component(hass, "ai_task", {})

    for entry in read_prerequisites():
        config_entry = MockConfigEntry(
            domain=entry.domain,
            data=entry.config_entry_data,
            options=entry.config_entry_options,
            version=entry.version or 1,
        )
        config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(config_entry.entry_id)
        assert config_entry.state == ConfigEntryState.LOADED


@pytest.fixture(name="agent")
def agent_fixture(
    configure_prerequisites: Any,
    rate_limited_agent: ConversationAgent,
    conversation_agent_config_entry: ConfigEntry,
) -> ConversationAgent:
    """Fixture to ensure the conversation agent and config entry are loaded."""
    return rate_limited_agent


@pytest.fixture(name="rate_limited_ai_task", scope="module")
def rate_limited_ai_task_fixture(
    model_config: ModelConfig,
) -> ConversationAgent:
    """Create the conversation agent.

    This is a module level fixture to ensure the rate limit is respected across
    individual test runs.
    """
    entity_id = "ai_task.mock_title"
    return create_ai_task_agent(entity_id, model_config.rpm)


@pytest.fixture(name="ai_task")
def ai_task_fixture(
    configure_prerequisites: Any,
    rate_limited_ai_task: ConversationAgent,
    conversation_agent_config_entry: ConfigEntry,
) -> ConversationAgent:
    """Fixture to ensure the conversation agent and config entry are loaded."""
    return rate_limited_ai_task
