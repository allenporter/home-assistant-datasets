"""Tests for the entity state diff module."""

from unittest.mock import Mock

from home_assistant_datasets.entity_state import EntityState
from home_assistant_datasets.entity_state.diff import EntityStateDiffFixture


ENTITY1_ON = EntityState(
    state="on",
    attributes={
        "brightness": 100,
        "color_mode": "brightness",
    },
)
ENTITY1_OFF = EntityState(
    state="off",
    attributes={
        "brightness": 100,
        "color_mode": "brightness",
    },
)
ENTITY1_DIM = EntityState(
    state="on",
    attributes={
        "brightness": 50,
        "color_mode": "brightness",
    },
)

ENTITY2_ON = EntityState(
    state="on",
    attributes={
        "color_mode": "rgbw",
    },
)
ENTITY2_OFF = EntityState(
    state="off",
    attributes={
        "color_mode": "rgbw",
    },
)


def test_no_diff() -> None:
    """Test the entity state diff routines."""

    mock_get_state = Mock()
    mock_get_state.get_state.return_value = {
        "light.kitchen": ENTITY1_ON,
        "light.front": ENTITY2_OFF,
    }

    diff = EntityStateDiffFixture(mock_get_state)
    diff.prepare({}, {})
    assert not diff.get_unexpected_changes()


def test_diff() -> None:
    """Test the entity state diff routines."""

    mock_get_state = Mock()
    mock_get_state.get_state.return_value = {
        "light.kitchen": ENTITY1_ON,
    }

    diff = EntityStateDiffFixture(mock_get_state)
    diff.prepare({}, {})

    mock_get_state.get_state.return_value = {
        "light.kitchen": ENTITY1_OFF,
    }

    assert diff.get_unexpected_changes() == {
        "light.kitchen": {
            "expected": {
                "state": "on",
            },
            "got": {
                "state": "off",
            },
        }
    }


def test_expected_change() -> None:
    """Test the entity state diff routines."""

    mock_get_state = Mock()
    mock_get_state.get_state.return_value = {
        "light.kitchen": ENTITY1_ON,
        "light.front": ENTITY2_ON,
    }

    diff = EntityStateDiffFixture(mock_get_state)
    diff.prepare(
        {
            "light.kitchen": EntityState(
                attributes={
                    "brightness": 50,
                }
            ),
            "light.front": EntityState(
                state="off",
            ),
        },
        {},
    )

    mock_get_state.get_state.return_value = {
        "light.kitchen": ENTITY1_DIM,
        "light.front": ENTITY2_OFF,
    }

    assert not diff.get_unexpected_changes()


def test_ignore_state_changes() -> None:
    """Test ignoring an entity diff in state change."""

    mock_get_state = Mock()
    mock_get_state.get_state.return_value = {
        "light.front": ENTITY2_ON,
    }

    diff = EntityStateDiffFixture(mock_get_state)
    diff.prepare({}, {"light.front": ["state"]})

    mock_get_state.get_state.return_value = {
        "light.front": ENTITY2_OFF,
    }

    assert not diff.get_unexpected_changes()


def test_ignore_attributes_changes() -> None:
    """Test ignoring an entity diff in attributes."""

    mock_get_state = Mock()
    mock_get_state.get_state.return_value = {
        "light.kitchen": ENTITY1_ON,
    }

    diff = EntityStateDiffFixture(mock_get_state)
    diff.prepare({}, {"light.kitchen": ["brightness"]})

    mock_get_state.get_state.return_value = {
        "light.kitchen": ENTITY1_DIM,
    }

    assert not diff.get_unexpected_changes()
