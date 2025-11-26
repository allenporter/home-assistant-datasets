"""Tests for blueprint schema conversion."""

from collections.abc import Generator
import datetime
import pathlib
import tempfile
from unittest.mock import patch

import pytest
from syrupy import SnapshotAssertion

from home_assistant_datasets.datasets.convert import blueprint_schema


def test_convert_blueprint(snapshot: SnapshotAssertion) -> None:
    """Test converting the blueprint schema to openapi format."""
    result = blueprint_schema.blueprint_openapi_schema()
    assert result == snapshot
