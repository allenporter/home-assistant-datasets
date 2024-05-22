"""Tests to validate the format of the area datasets."""

import pathlib

import pytest
import yaml


AREA_FILES = [
    filename
    for filename in pathlib.Path("datasets/areas/").glob("*.yaml")
]


@pytest.mark.parametrize(
    ("filename"),
    [
        (filename) for filename in AREA_FILES
    ],
    ids=(
        str(filename) for filename in AREA_FILES
    )
)
def test_areas(filename: pathlib.Path) -> None:
    """Test that the area datasets are formatted properpy."""

    document = yaml.load(filename.read_text(), Loader=yaml.SafeLoader)
    assert "name" in document

    # All homes have at least one area
    assert "areas" in document
    assert len(document["areas"]) > 0
