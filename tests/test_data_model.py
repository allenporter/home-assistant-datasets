"""Tests to validate the datamodel parsers."""

import dataclasses
from unittest.mock import patch

from syrupy import SnapshotAssertion

from home_assistant_datasets import data_model


def test_models(snapshot: SnapshotAssertion) -> None:
    """Test the data_model model card parsing."""
    with patch("home_assistant_datasets.secrets.get_secret", return_value="SECRET"):
        model_cards = data_model.read_models()

    assert [dataclasses.asdict(model) for model in model_cards.models] == snapshot


def test_dataset_cards(snapshot: SnapshotAssertion) -> None:
    """Test the data_model dataset card parsing."""
    dataset_cards = data_model.read_dataset_cards()
    assert dataset_cards == snapshot
