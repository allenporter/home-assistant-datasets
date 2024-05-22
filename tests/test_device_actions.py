"""Tests to validate the format of the devices action datasets."""

import pathlib

import pytest
import synthetic_home.device_types
import synthetic_home.synthetic_home
import yaml
import synthetic_home


DEVICE_ACTION_FILES = [
    filename
    for filename in pathlib.Path("datasets/device-actions/").glob("*.yaml")
]


@pytest.mark.parametrize(
    ("filename"),
    [
        (filename) for filename in DEVICE_ACTION_FILES
    ],
    ids=(
        str(filename) for filename in DEVICE_ACTION_FILES
    )
)
def test_device_actions(filename: pathlib.Path) -> None:
    """Test that the device action datasets are formatted properly."""

    registry = synthetic_home.device_types.load_device_type_registry()

    documents = yaml.load_all(filename.read_text(), Loader=yaml.SafeLoader)
    for document in documents:
        assert "home" in document

        device = document.get("device")
        assert device
        assert "name" in device
        assert "area" in device
        device_type = device.get("device_type")
        assert device_type
        assert device_type in registry.device_types

        device_states = [ state.name for state in registry.device_types[device_type].device_states ]

        actions = document.get("actions")
        assert actions
        for action in actions:
            assert "sentences" in action
            device_state = action.get("device_state")
            assert device_state in device_states
            expected_device_state = action.get("expected_device_state")
            assert expected_device_state in device_states
