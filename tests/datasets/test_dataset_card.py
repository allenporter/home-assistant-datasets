"""Tests to validate the datamodel parsers."""

from syrupy import SnapshotAssertion

from home_assistant_datasets.datasets.dataset_card import read_dataset_cards


def test_dataset_cards(snapshot: SnapshotAssertion) -> None:
    """Test the data_model dataset card parsing."""
    dataset_cards = read_dataset_cards()
    assert dataset_cards == snapshot
