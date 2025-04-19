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
from custom_components import synthetic_home  # noqa: F401


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
