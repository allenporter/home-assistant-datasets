"""Tests to validate the format of the devices action datasets."""

import pathlib

import pytest
import synthetic_home.device_types
import synthetic_home.synthetic_home
import yaml
import synthetic_home


DEVICES_DIR = pathlib.Path("datasets/devices/")
DEVICE_ACTION_FILES = [
    filename for filename in pathlib.Path("datasets/device-actions/").glob("*.yaml")
]


@pytest.mark.parametrize(
    ("filename"),
    [(filename) for filename in DEVICE_ACTION_FILES],
    ids=(str(filename) for filename in DEVICE_ACTION_FILES),
)
def test_device_actions(filename: pathlib.Path) -> None:
    """Test that the device action datasets are formatted properly."""

    registry = synthetic_home.device_types.load_device_type_registry()

    documents = yaml.load_all(filename.read_text(), Loader=yaml.SafeLoader)
    for document in documents:
        home_id = document.get("home")
        assert home_id

        home_yaml = DEVICES_DIR / f"{home_id}.yaml"
        home_document = documents = yaml.load(
            home_yaml.read_text(), Loader=yaml.SafeLoader
        )
        assert home_document["name"]

        actions = document.get("actions")
        assert actions
        for action in actions:
            assert "sentences" in action

            device_states = action.get("device_states")
            assert isinstance(device_states, list)
            for device_state in device_states:
                name = device_state.get("name")
                assert name
                area = device_state.get("area")
                assert area
                state = device_state.get("state")
                assert state

                found_device = next(
                    iter(
                        [
                            device
                            for device in home_document["devices"].get(area, [])
                            if device["name"] == name
                        ]
                    )
                )
                assert found_device
                device_type = found_device.get("device_type")
                found_states = [
                    state.name
                    for state in registry.device_types[device_type].device_states
                ]
                assert state in found_states

            expected_device_states = action.get("expected_device_states")
            assert isinstance(expected_device_states, list)
            for device_state in expected_device_states:
                name = device_state.get("name")
                assert name
                area = device_state.get("area")
                assert area
                state = device_state.get("state")
                assert state

                found_device = next(
                    iter(
                        [
                            device
                            for device in home_document["devices"].get(area, [])
                            if device["name"] == name
                        ]
                    )
                )
                assert found_device
                device_type = found_device.get("device_type")
                found_states = [
                    state.name
                    for state in registry.device_types[device_type].device_states
                ]
                assert state in found_states
