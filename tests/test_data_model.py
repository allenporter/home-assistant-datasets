"""Tests to validate the datamodel parsers."""

from unittest.mock import patch

from home_assistant_datasets import data_model


def test_models() -> None:
    """Test the data_model model card parsing."""
    with patch("home_assistant_datasets.secrets.get_secret", return_value="SECRET"):
        assert data_model.read_models()


def test_dataset_cards() -> None:
    """Test the data_model dataset card parsing."""
    assert data_model.read_dataset_cards()
