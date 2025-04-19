"""Tests to validate the datamodel parsers."""

import dataclasses
from unittest.mock import patch

from syrupy import SnapshotAssertion

from home_assistant_datasets.models import read_models


def test_models(snapshot: SnapshotAssertion) -> None:
    """Test the data_model model card parsing."""
    read_models.cache_clear()
    with patch("home_assistant_datasets.secrets.get_secret", return_value="SECRET"):
        model_cards = read_models()

    assert [dataclasses.asdict(model) for model in model_cards.models] == snapshot
