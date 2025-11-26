"""Tests for blueprint schema conversion."""

from syrupy import SnapshotAssertion

from home_assistant_datasets.datasets.convert import blueprint_schema


def test_convert_blueprint(snapshot: SnapshotAssertion) -> None:
    """Test converting the blueprint schema to openapi format."""
    result = blueprint_schema.blueprint_openapi_schema()
    assert result == snapshot
