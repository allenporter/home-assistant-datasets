"""Test library for converting intents."""

from collections.abc import Generator
import datetime
import pathlib
import tempfile
from unittest.mock import patch

import pytest
from syrupy import SnapshotAssertion

from home_assistant_datasets.datasets.convert import intents

TESTDATA = pathlib.Path("tests/datasets/convert/testdata/intents")


@pytest.fixture(name="tmpdir")
def tmpdir_fixture() -> Generator[pathlib.Path]:
    """Fixture to produce a temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)


@pytest.mark.parametrize(
    ("filename", "expected_domain", "expected_intent"),
    [
        ("cover_HassTurnOn.yaml", "cover", "HassTurnOn"),
        (
            "shopping_list_HassShoppingListAddItem.yaml",
            "shopping_list",
            "HassShoppingListAddItem",
        ),
    ],
)
def test_fixture_filename_parts(
    filename: pathlib.Path, expected_domain: str, expected_intent: str
) -> None:
    """Tests for fixture_filename_parts."""
    assert intents.fixture_filename_parts(pathlib.Path(filename)) == (
        expected_domain,
        expected_intent,
    )


def test_convert_intent_tests(
    tmpdir: pathlib.Path, snapshot: SnapshotAssertion
) -> None:
    """Test converting the intent tests to assist datasets."""
    FIXED_DATE = datetime.datetime(2025, 4, 20, 17, 20)

    with patch("home_assistant_datasets.datasets.convert.intents.now") as mock_now:
        mock_now.return_value = FIXED_DATE
        intents.convert_intent_tests(TESTDATA, tmpdir)
    found_files = [file for file in sorted(list(tmpdir.glob("**"))) if not file.is_dir()]
    assert [file.relative_to(tmpdir) for file in found_files] == snapshot

    for found_file in found_files:
        assert found_file.read_text() == snapshot
