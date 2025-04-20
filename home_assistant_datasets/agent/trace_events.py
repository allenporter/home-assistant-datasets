"""The trace_events module is related to events captured when scraping model outputs.

This is used during the collect phase during the conversation agent calls to
capture runtime data or tracing such as details of the conversation or other
stats.

This can also be used in the evaluation state to interpret the collected
model outputs or tracing.
"""

import dataclasses
from dataclasses import dataclass
from typing import Any

from homeassistant.components.conversation import trace


__all__ = [
    "TokenStats",
    "TokenStatsBank",
    "find_llm_call",
    "find_token_stats",
]


@dataclass(frozen=True, kw_only=True)
class TokenStats:
    """Class for token stats."""

    input_tokens: int | float
    cached_input_tokens: int | float
    output_tokens: int | float
    duration_ms: float = 0
    n_count: int | float = 1
    """Total raw number of requests, which may be more than number of tasks."""


class TokenStatsBank:
    """Class for summarizing TokenStats across a bunch of runs."""

    def __init__(self) -> None:
        """Initialize report."""
        self.stats: list[TokenStats] = []

    def append(self, stats: TokenStats) -> None:
        """Append a token stats record."""
        self.stats.append(stats)

    def summary_data(self) -> dict[str, Any]:
        """Return a summary of the token stats as a dictionary."""
        return {
            "token_avg": dataclasses.asdict(self.avg()),
            "token_sum": dataclasses.asdict(self.sum()),
            "token_input_cache_ratio": round(
                sum(s.cached_input_tokens for s in self.stats)
                / sum(s.input_tokens for s in self.stats),
                2,
            ),
        }

    def avg(self) -> TokenStats:
        """Average the number of tokens across tasks."""
        return TokenStats(
            input_tokens=round(
                sum(s.input_tokens for s in self.stats) / len(self.stats), 2
            ),
            cached_input_tokens=round(
                sum(s.cached_input_tokens for s in self.stats) / len(self.stats), 2
            ),
            output_tokens=round(
                sum(s.output_tokens or 0 for s in self.stats) / len(self.stats), 2
            ),
            duration_ms=round(
                sum(s.duration_ms for s in self.stats) / len(self.stats), 2
            ),
            n_count=round(sum(s.n_count for s in self.stats) / len(self.stats), 2),
        )

    def sum(self) -> TokenStats:
        """Sum the token stats across tasks."""
        return TokenStats(
            input_tokens=sum(s.input_tokens for s in self.stats),
            cached_input_tokens=sum(s.cached_input_tokens for s in self.stats),
            output_tokens=sum(s.output_tokens or 0 for s in self.stats),
            duration_ms=sum(s.duration_ms for s in self.stats),
            n_count=sum(s.n_count for s in self.stats),
        )


def find_token_stats(
    trace_events: list[dict[str, Any]], duration_ms: float
) -> TokenStats | None:
    """Gets the agent detail that contains conversation agent statistics."""
    stats_data = list(
        stats
        for event in trace_events
        if event["event_type"] == trace.ConversationTraceEventType.AGENT_DETAIL
        and (stats := event["data"].get("stats")) is not None
    )
    if not stats_data:
        return None
    bank = TokenStatsBank()
    for stats in stats_data:
        bank.append(
            TokenStats(
                input_tokens=stats.get("input_tokens", 0),
                cached_input_tokens=stats.get("cached_input_tokens", 0),
                output_tokens=stats.get("output_tokens", 0),
                duration_ms=duration_ms,
            )
        )
        duration_ms = 0
    return bank.sum()


def find_llm_call(trace_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Gets the llm call from the conversation trace."""
    tool_call = next(
        iter(
            event
            for event in trace_events
            if event["event_type"]
            # type: ignore[attr-defined]
            in (trace.ConversationTraceEventType.TOOL_CALL, "llm_tool_call")
        ),
        None,
    )
    if tool_call is None:
        return None

    data = tool_call["data"]
    return {
        "tool_name": data.get("tool_name"),
        "tool_args": data.get("tool_args"),
    }


def token_stats_from_context(context: dict[str, Any]) -> TokenStats | None:
    """Extract the TokenStats from the collection context."""
    return find_token_stats(
        context.get("conversation_trace", {}), duration_ms=context.get("duration_ms", 0)
    )
