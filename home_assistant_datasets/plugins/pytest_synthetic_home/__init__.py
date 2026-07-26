"""Test fixtures for setting up a synthetic home.

Tests must provide a fixture `synthetic_home_config` which is a path to the yaml
fixture file. The contents of the synthetic home inventory/fixture will be loaded
into the synthetic home custom component.
"""

from collections.abc import AsyncGenerator, Generator
import logging
import pathlib
from unittest.mock import patch, mock_open

import pytest
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState, ConfigEntry
from homeassistant.setup import async_setup_component
import sys
import pytest_homeassistant_custom_component

tc_dir = (
    pathlib.Path(pytest_homeassistant_custom_component.__file__).parent
    / "testing_config"
)
if str(tc_dir) not in sys.path:
    sys.path.append(str(tc_dir))

sh_dir = (pathlib.Path(__file__).parents[3] / "home-assistant-synthetic-home").resolve()
sh_cc = str(sh_dir / "custom_components")
if sh_dir.exists():
    try:
        import custom_components

        if hasattr(custom_components, "__path__"):
            if sh_cc in custom_components.__path__:
                custom_components.__path__.remove(sh_cc)
            custom_components.__path__.insert(0, sh_cc)
    except Exception:
        pass

if "custom_components.synthetic_home" in sys.modules:
    del sys.modules["custom_components.synthetic_home"]

from custom_components import synthetic_home  # noqa: E402, F401


_LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(
    enable_custom_integrations: None,
) -> Generator[None, None, None]:
    """Enable custom integration."""
    _ = enable_custom_integrations  # unused
    yield


@pytest.fixture(autouse=True)
async def mock_default_components(hass: HomeAssistant) -> None:
    """Fixture to setup required default components."""
    assert await async_setup_component(hass, "homeassistant", {})


@pytest.fixture(name="synthetic_home_config")
def mock_synthetic_home_config() -> str | None:
    """Fixture to load the synthetic home config."""
    return None


@pytest.fixture(name="synthetic_home_yaml")
def mock_synthetic_home_content(synthetic_home_config: str | None) -> str | None:
    """Mock out the yaml config file contents."""
    if synthetic_home_config is None:
        return None
    with pathlib.Path(synthetic_home_config).absolute().open("r") as f:
        return f.read()


@pytest.fixture(autouse=True, name="synthetic_home_config_entry")
async def mock_synthetic_home(
    hass: HomeAssistant, synthetic_home_yaml: str | None
) -> AsyncGenerator[ConfigEntry | None, None]:
    """Fixture for mock configuration entry."""
    if synthetic_home_yaml is None:
        yield None
        return

    # TODO(#12): Support loading from the custom component or core development environment
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    config_entry = MockConfigEntry(
        domain="synthetic_home", data={"config_filename": "ignored"}
    )
    config_entry.add_to_hass(hass)

    with (
        patch(
            "synthetic_home.inventory.read_config_content",
            mock_open(read_data=synthetic_home_yaml),
        ),
        # Performance improvements during evaluation
        patch("custom_components.synthetic_home.cover.COVER_INSTANT", True),
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        assert config_entry.state == ConfigEntryState.LOADED

        import synthetic_home.inventory as inv  # noqa: E402
        from homeassistant.helpers import (  # noqa: E402
            area_registry as ar,
            device_registry as dr,
        )

        inv_obj = inv.decode_inventory(synthetic_home_yaml)

        area_reg = ar.async_get(hass)
        areas = (
            inv_obj.areas.values()
            if isinstance(inv_obj.areas, dict)
            else (inv_obj.areas or [])
        )
        for area in areas:
            area_reg.async_get_or_create(area.name)

        device_reg = dr.async_get(hass)
        devices = (
            inv_obj.devices.values()
            if isinstance(inv_obj.devices, dict)
            else (inv_obj.devices or [])
        )
        for device in devices:
            device_reg.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                identifiers={("synthetic_home", device.id)},
                name=device.name,
                manufacturer=device.info.manufacturer
                if device.info and hasattr(device.info, "manufacturer")
                else None,
                model=device.info.model
                if device.info and hasattr(device.info, "model")
                else None,
                sw_version=device.info.sw_version
                if device.info and hasattr(device.info, "sw_version")
                else None,
                suggested_area=device.area,
            )

        yield config_entry
        await hass.config_entries.async_unload(config_entry.entry_id)


@pytest.fixture(autouse=True)
def validate_entities(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    synthetic_home_yaml: str,
) -> None:
    """Fixture to verify that all entities are property created by synthetic home to avoid misconfiguration."""
    assert synthetic_home_config_entry.state is ConfigEntryState.LOADED

    inventory = yaml.load(synthetic_home_yaml, Loader=yaml.Loader)
    assert inventory
    if not (entities := inventory.get("entities")):
        raise ValueError(
            f"No entities were specified in the inventory file: {inventory.keys()}"
        )
    for entity in entities:
        entity_id = entity["id"]
        state = hass.states.get(entity_id)
        assert state, f"Entity id not created {entity_id}"
        assert state.state != "unavailable"
        assert state.state not in (
            "unavailable",
            "unknown",
        ), f"Entity id has unavailable state {entity_id}: {state.state}"
