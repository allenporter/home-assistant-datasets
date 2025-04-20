"""Test library for converting intents."""

from collections.abc import Generator
import pathlib
import tempfile

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


def test_parse_fixtures_as_inventory(
    tmpdir: pathlib.Path, snapshot: SnapshotAssertion
) -> None:
    """Test parsing the fixtures as an inventory file."""

    intents.convert_intent_tests(TESTDATA, tmpdir)
    found_files = [file for file in list(tmpdir.glob("**")) if not file.is_dir()]
    assert [file.relative_to(tmpdir) for file in found_files] == snapshot

    for found_file in found_files:
        assert found_file.read_text() == snapshot
