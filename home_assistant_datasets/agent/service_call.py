"""The default conversation agent implemented with a service call."""

import datetime
import logging
from typing import Any

from homeassistant.core import HomeAssistant, Context
from homeassistant.components.conversation import trace
from homeassistant.helpers import llm

from .agent import ConversationAgent


__all__ = [
    "create_agent",
]

_LOGGER = logging.getLogger(__name__)


def dump_conversation_trace(trace: trace.ConversationTrace) -> list[dict[str, Any]]:
    """Serialize the conversation trace for evaluation."""
    trace_data = trace.as_dict()
    trace_events = trace_data["events"]
    result = []
    for trace_event in trace_events:
        trace_event_data = trace_event["data"]
        data = {}
        for k, v in trace_event_data.items():
            if isinstance(v, Context):
                v = dict(v.as_dict())
            if isinstance(v, list) and v and isinstance(v[0], llm.Tool):
                v = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": str(tool.parameters),
                    }
                    for tool in v
                ]
            data[k] = v
        values: dict[str, Any] = {
            "event_type": str(trace_event["event_type"]),
            "data": data,
        }
        if ts_str := trace_event.get("timestamp"):
            values["timestamp"] = datetime.datetime.fromisoformat(ts_str)
        result.append(values)
    return result


class ServiceCall(ConversationAgent):
    """A client library for a conversation agent service call."""

    def __init__(self, agent_id: str) -> None:
        """Initialize the agent."""
        self._agent_id = agent_id

    async def async_process(self, hass: HomeAssistant, text: str) -> str:
        """Process a text input and return the response."""
        _LOGGER.debug("hass.services.async_call=%s", hass.services.async_call)
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

    def trace_context(self) -> dict[str, Any]:
        """Record any relevant trace context captured during the requests."""
        conversation_trace = []
        if (traces := trace.async_get_traces()) and (last_trace := traces[-1]):
            conversation_trace = dump_conversation_trace(last_trace)
        return {
            "conversation_trace": conversation_trace,
        }


def create_agent(agent_id: str) -> ConversationAgent:
    """Create a conversation agent service call wrapper."""
    return ServiceCall(agent_id)
