"""A wrapper to make a conversation agent retryable."""

import datetime
import logging
from typing import Any

from homeassistant.core import HomeAssistant

from .agent import ConversationAgent


__all__ = [
    "timed_agent",
]


_LOGGER = logging.getLogger(__name__)


class TimedAgent(ConversationAgent):
    """A conversation agent wrapper that tracks called durations."""

    def __init__(self, agent: ConversationAgent) -> None:
        """Initialize the agent."""
        self._agent = agent
        self._elapsed: datetime.timedelta | None = None

    async def async_process(
        self,
        hass: HomeAssistant,
        text: str,
        *,
        structure: Any | None = None,
    ) -> str:
        """Process a text input and return the response."""
        start = datetime.datetime.now()
        try:
            return await self._agent.async_process(hass, text, structure=structure)
        finally:
            self._elapsed = datetime.datetime.now() - start

    def trace_context(self) -> dict[str, Any]:
        """Record any relevant trace context captured during the requests."""
        context = self._agent.trace_context()
        if self._elapsed is not None:
            duration_ms = self._elapsed / datetime.timedelta(milliseconds=1)
            context["duration_ms"] = duration_ms
        return context


def timed_agent(agent: ConversationAgent) -> ConversationAgent:
    """Factory function that wraps the conversation agent with the timer."""
    return TimedAgent(agent)
