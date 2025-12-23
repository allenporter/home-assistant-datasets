"""Tests to validate the datamodel parsers."""

from unittest.mock import patch

from syrupy.assertion import SnapshotAssertion

from home_assistant_datasets.models import read_models


def test_models(snapshot: SnapshotAssertion) -> None:
    """Test the data_model model card parsing."""
    read_models.cache_clear()
    with patch("home_assistant_datasets.secrets.get_secret", return_value="SECRET"):
        model_cards = read_models()

    # Pick an arbitrary model to validate
    assert len(model_cards.models) > 5
    model = next(
        iter(
            model for model in model_cards.models if model.model_id == "gemini-2.5-pro"
        )
    )
    assert model == snapshot
