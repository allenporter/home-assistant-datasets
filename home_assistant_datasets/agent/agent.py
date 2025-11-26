"""Conversation agent module."""

from abc import ABC, abstractmethod
from typing import Any

from homeassistant.core import HomeAssistant


class ConversationAgent(ABC):
    """A simple client library for calling a conversation agent."""

    @abstractmethod
    async def async_process(
        self,
        hass: HomeAssistant,
        text: str,
        *,
        structure: Any | None = None,
    ) -> str:
        """Process a text input and return the response."""

    @abstractmethod
    def trace_context(self) -> dict[str, Any]:
        """Record any relevant trace context captured during the requests."""
