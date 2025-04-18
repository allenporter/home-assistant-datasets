"""Rate limiter to avoid throttling from APIs."""

from typing import Any

from pyrate_limiter import (
    Duration,
    Rate,
    Limiter,
)

from homeassistant.core import HomeAssistant

from .agent import ConversationAgent

__all__ = [
    "wrap_rate_limit",
]

MAX_DELAY = 60 * 1000  # 1 minute


def _create_limiter(rpm: int) -> Limiter:
    """Create a rate limiter."""
    rate = Rate(rpm, Duration.MINUTE)
    return Limiter(rate, max_delay=MAX_DELAY)


class RateLimitedAgent(ConversationAgent):
    """A client library for a conversation agent service call."""

    def __init__(self, agent: ConversationAgent, rate_limiter: Limiter) -> None:
        """Initialize the agent."""
        self._agent = agent
        self._rate_limiter = rate_limiter

    async def async_process(self, hass: HomeAssistant, text: str) -> str:
        """Process a text input and return the response."""
        if self._rate_limiter:
            await self._rate_limiter.try_acquire("item")  # type: ignore[misc]
        return await self._agent.async_process(hass, text)

    def trace_context(self) -> dict[str, Any]:
        """Record any relevant trace context captured during the requests."""
        return self._agent.trace_context()


def wrap_rate_limit(agent: ConversationAgent, rpm: int) -> ConversationAgent:
    """Rate limit the specified agent.

    Note that this should be long lived in order for rate limiting to be effective.
    """
    return RateLimitedAgent(agent, _create_limiter(rpm))
