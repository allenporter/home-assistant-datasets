"""Tests for the trace_events module."""

from syrupy import SnapshotAssertion

from home_assistant_datasets.agent.trace_events import TokenStats, TokenStatsBank


def test_token_stats_bank(snapshot: SnapshotAssertion) -> None:
    """Tests for TokenStatsBank."""

    bank = TokenStatsBank()
    bank.append(
        TokenStats(
            input_tokens=500,
            cached_input_tokens=100,
            output_tokens=250,
        )
    )
    bank.append(
        TokenStats(
            input_tokens=500,
            cached_input_tokens=100,
            output_tokens=250,
        )
    )
    assert bank.summary_data() == snapshot
