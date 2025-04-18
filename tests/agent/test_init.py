"""Tests for the agent module."""

from unittest.mock import AsyncMock

from homeassistant.exceptions import HomeAssistantError

from home_assistant_datasets.agent import create_default_agent


RESPONSE = {"response": {"speech": {"plain": {"speech": "Paris."}}}}


async def test_create_default_agent() -> None:
    """Tests for the default conversation agent."""

    agent = create_default_agent("mock_agent_id")

    mock_hass = AsyncMock()
    mock_hass.services.async_call.return_value = RESPONSE

    response = await agent.async_process(mock_hass, "What is the capital of france?")

    assert response == "Paris."

    # Just ensure it can run without failing
    agent.trace_context()


async def test_create_default_agent_error() -> None:
    """Tests for the default conversation agent."""

    agent = create_default_agent("mock_agent_id")

    mock_hass = AsyncMock()
    mock_hass.services.async_call.side_effect = HomeAssistantError("Fail")

    response = await agent.async_process(mock_hass, "What is the capital of france?")

    assert response == "Fail"

    # Just ensure it can run without failing
    agent.trace_context()
