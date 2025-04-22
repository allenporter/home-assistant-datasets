"""A wrapper to make a conversation agent retryable."""

import asyncio
import logging
import json
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from .agent import ConversationAgent

__all__ = [
    "wrap_retryable",
]


_LOGGER = logging.getLogger(__name__)


TIMEOUT = 40
MAX_TRIES = 3


class RetryableAgent(ConversationAgent):
    """A retryable conversation agent wrapper."""

    def __init__(self, agent: ConversationAgent) -> None:
        """Initialize the agent."""
        self._agent = agent
        self._tries = 0

    async def async_process(self, hass: HomeAssistant, text: str) -> str:
        """Process a text input and return the response."""
        # Run the conversation agent
        self._tries = 0
        response = ""
        retryable = True
        while self._tries < MAX_TRIES and retryable:
            self._tries += 1
            retryable = False
            _LOGGER.debug("Prompt: %s", text)
            try:
                async with asyncio.timeout(TIMEOUT):
                    response = await self._agent.async_process(hass, text)
            except (
                HomeAssistantError,
                ServiceValidationError,
                TypeError,
                json.JSONDecodeError,
            ) as err:
                response = str(err)
            except (TimeoutError, asyncio.CancelledError):
                _LOGGER.debug("Timeout error (tries=%s)", self._tries)
                response = f"Timeout (after {self._tries} tries)"
                retryable = True
            await hass.async_block_till_done()
            _LOGGER.debug("Response: %s", response)

        return response

    def trace_context(self) -> dict[str, Any]:
        """Record any relevant trace context captured during the requests."""
        context = self._agent.trace_context()
        context["tries"] = self._tries
        return context


def wrap_retryable(agent: ConversationAgent) -> ConversationAgent:
    """Wrap the agent with retry logic, returning errors as text."""
    return RetryableAgent(agent)
