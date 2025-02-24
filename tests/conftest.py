"""Test fixttures for home-assistant-datasets."""

import pytest
import pathlib

from syrupy import SnapshotAssertion
from syrupy.extensions.amber import AmberSnapshotExtension
from syrupy.location import PyTestLocation


DIFFERENT_DIRECTORY = "snapshots"


class DifferentDirectoryExtension(AmberSnapshotExtension):
    """Extension to set a different snapshot directory."""

    @classmethod
    def dirname(cls, *, test_location: "PyTestLocation") -> str:
        """Override the snapshot directory name."""
        return str(
            pathlib.Path(test_location.filepath).parent.joinpath(DIFFERENT_DIRECTORY)
        )


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Fixture to override the snapshot directory."""
    return snapshot.use_extension(DifferentDirectoryExtension)
