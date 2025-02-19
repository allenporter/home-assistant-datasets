"""Fixtures for exercising automation solutions."""

import datetime
from collections.abc import Generator, Callable
import pathlib
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component


FIXTURES = "_fixtures.yaml"
SOLUTION = "solution.yaml"


@pytest.fixture(name="test_path")
def test_path_fixture(request):
    """Fixture to get the dataset name from the currently running test."""
    return pathlib.Path(request.module.__file__).parent


@pytest.fixture
def synthetic_home_yaml(test_path: pathlib.Path) -> str:
    """Fixture to load synthetic home entities."""
    return (test_path / FIXTURES).read_text()


@pytest.fixture(autouse=True)
def expected_lingering_tasks() -> bool:
    """Fixtures to avoid tasks around store shutdown."""
    return True


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


def generate_blueprint_paths() -> str:
    """Generate theblueprint paths to use when testing."""
    return [str(SOLUTION)]


@pytest.fixture(
    name="blueprint_path",
    params=generate_blueprint_paths(),
)
def blueprint_path_fixture(test_path: pathlib.Path, request) -> str:
    """Fixture with the name of the blueprint file to load."""
    return str(test_path / request.param)


@pytest.fixture(autouse=True)
async def automation_fixture(
    hass: HomeAssistant, automation_config: dict[str, Any]
) -> None:
    """Fixture to set up the blueprint."""
    assert await async_setup_component(
        hass, "automation", {"automation": [automation_config]}
    )
    await hass.async_block_till_done()
