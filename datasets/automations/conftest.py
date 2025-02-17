"""Fixtures for exercising automation solutions."""

import datetime
from collections.abc import Generator, Callable

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util
from homeassistant.helpers import entity_registry as er


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Fixtures to avoid timers around store shutdown."""
    return True


@pytest.fixture(autouse=True)
def restore_tz() -> Generator[None, None, None]:
    """Fix Home Assistant teardown happening too soon."""
    yield
    dt_util.set_default_time_zone(datetime.UTC)


@pytest.fixture(name="get_state")
def get_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> Callable[[], dict[str, str]]:
    """Fixture that can state for all synthetic home entities."""

    def func() -> dict[str, str]:
        entity_entries = er.async_entries_for_config_entry(
            entity_registry, synthetic_home_config_entry.entry_id
        )
        return {
            entity_entry.entity_id: hass.states.get(entity_entry.entity_id).state
            for entity_entry in entity_entries
        }

    return func
