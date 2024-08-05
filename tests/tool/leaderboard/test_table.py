"""Functions for testing the internals of the leaderboard tables."""

from home_assistant_datasets.tool.leaderboard import table


def test_table() -> None:
    """Test creating a color map for a set of values."""

    assert (
        table.table(
            ["col 1", "col 2"],
            [
                ["a", "b"],
                ["c", "d"],
            ],
        )
        == """| col 1 | col 2 |
| --- | --- |
| a | b |
| c | d |"""
    )
