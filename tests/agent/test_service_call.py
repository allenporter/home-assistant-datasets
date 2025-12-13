"""Tests for the service_call module.

We pick an arbitrary LLM provider to mock out to test the service call.
"""

from collections.abc import Generator
import logging
from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.components import conversation

from home_assistant_datasets.agent import ConversationAgent
from home_assistant_datasets.agent.service_call import ServiceCall

_LOGGER = logging.getLogger(__name__)

pytest_plugins = [
    "home_assistant_datasets.plugins.pytest_agent",
]


@pytest.fixture(name="mock_gemini_client", autouse=True)
async def mock_gemini_client_fixture() -> Generator[None, None, None]:
    """Mock out any calls to the real Gemini Client"""
    with patch(
        "homeassistant.components.google_generative_ai_conversation.Client",
    ) as mock_gemini_client:
        mock_gemini_client.return_value.aio = AsyncMock()
        yield


@pytest.fixture(name="mock_handle_chat_log")
async def mock_handle_chat_log_fixture(
    hass: HomeAssistant,
) -> Generator[Mock, None, None]:
    """Mock out the chat log handler to return a fixed response."""
    with patch(
        "homeassistant.components.google_generative_ai_conversation.entity.GoogleGenerativeAILLMBaseEntity._async_handle_chat_log"
    ) as mock_handle_chat_log:
        assert await async_setup_component(
            hass, "google_generative_ai_conversation", {}
        )

        yield mock_handle_chat_log


@pytest.fixture(name="model_id", scope="module")
def model_id_fixture() -> str:
    return "gemini-2.5-flash"


async def test_agent(
    hass: HomeAssistant, agent: ConversationAgent, mock_handle_chat_log: Mock
) -> None:
    """Test the service call agent."""

    async def fake_text_response(chat_log: conversation.ChatLog, *args, **kwargs):
        async for tool_call_result in chat_log.async_add_assistant_content(
            conversation.AssistantContent(
                agent_id="conversation.mock_title",
                content="Hello there!",
            )
        ):
            _LOGGER.debug("Ignoring tool calls in mock handler: %s", tool_call_result)

    mock_handle_chat_log.side_effect = fake_text_response

    service_call = ServiceCall(agent_id="conversation.mock_title")
    result = await service_call.async_process(hass, "Hello, World!")
    assert result == "Hello there!"
