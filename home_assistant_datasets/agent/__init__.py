"""Conversation agent module.

This module is a thin wrapper around the Conversation Agent process service,
tied to a simple interface to handle things like rate limiting, timing,
and retries.

This module is primarily used during data collection / scraping.
"""

from . import rate_limit, retryable, service_call, timing, ai_task
from .agent import ConversationAgent


__all__ = [
    "ConversatioAgent",
    "AITask",
    "create_default_agent",
    "trace_events",
    "service_call",
    "rate_limit",
    "retryable",
    "timing",
]


def create_default_agent(
    conversation_agent_id: str, rpm: int | None = None
) -> ConversationAgent:
    """Create the conversation agent client id.

    Note that this should be long lived in order for rate limiting to be effective.
    """
    agent = service_call.create_agent(conversation_agent_id)
    agent = timing.timed_agent(agent)
    if rpm:
        agent = rate_limit.wrap_rate_limit(agent, rpm)
    agent = retryable.wrap_retryable(agent)
    return agent


def create_ai_task_agent(
    entity_id: str, rpm: int | None = None
) -> ConversationAgent:
    """Create the conversation agent client id.

    Note that this should be long lived in order for rate limiting to be effective.
    """
    agent = ai_task.create_ai_task_agent(entity_id)
    agent = timing.timed_agent(agent)
    if rpm:
        agent = rate_limit.wrap_rate_limit(agent, rpm)
    agent = retryable.wrap_retryable(agent)
    return agent
