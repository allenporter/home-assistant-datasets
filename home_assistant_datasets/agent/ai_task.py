"""The default conversation agent implemented with a service call."""

import logging
from typing import Any
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.components.conversation import trace
from homeassistant.components.ai_task import async_generate_data

from .agent import ConversationAgent
from .service_call import dump_conversation_trace


__all__ = [
    "create_ai_task_agent",
]

_LOGGER = logging.getLogger(__name__)


class AITask(ConversationAgent):
    """A client library for an agent implemented using AITask."""

    def __init__(self, entity_id: str) -> None:
        """Initialize the agent."""
        self._entity_id = entity_id

    async def async_process(
        self,
        hass: HomeAssistant,
        text: str,
        *,
        structure: Any | None = None,
    ) -> str:
        """Process a text input and return the response."""
        result = await async_generate_data(
            hass,
            entity_id=self._entity_id,
            task_name="home-assistant-datasets-benchmark",
            instructions=text,
            structure=structure,
        )
        return yaml.dump(result.data)  # type: ignore[no-any-return]

    def trace_context(self) -> dict[str, Any]:
        """Record any relevant trace context captured during the requests."""
        conversation_trace = []
        if (traces := trace.async_get_traces()) and (last_trace := traces[-1]):
            conversation_trace = dump_conversation_trace(last_trace)
        return {
            "conversation_trace": conversation_trace,
        }


def create_ai_task_agent(entity_id: str) -> ConversationAgent:
    """Create a conversation agent service call wrapper."""
    return AITask(entity_id)
