"""Tests to validate the format of the devices datasets."""

import pathlib

import pytest
import synthetic_home.device_types
import synthetic_home.synthetic_home
import yaml
import synthetic_home


DEVICE_FILES = [
    filename
    for filename in pathlib.Path("datasets/devices/").glob("*.yaml")
]


@pytest.mark.parametrize(
    ("filename"),
    [
        (filename) for filename in DEVICE_FILES
    ],
    ids=(
        str(filename) for filename in DEVICE_FILES
    )
)
def test_devices(filename: pathlib.Path) -> None:
    """Test that the device datasets are formatted properly."""

    registry = synthetic_home.device_types.load_device_type_registry()


    document = yaml.load(filename.read_text(), Loader=yaml.SafeLoader)
    assert "name" in document

    # All homes have at least one area
    assert "areas" in document
    assert len(document["areas"]) > 0

    # Devices are present and have a valid device type
    area_devices = document.get("devices", [])
    assert area_devices
    for area, devices in area_devices.items():
        for device in devices:
            device_type = device.get("device_type")
            assert device_type
            assert device_type in registry.device_types
