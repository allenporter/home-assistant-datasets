"""Tests for the synthetic home pytest plugin."""

from typing import Any


PLUGINS = ["home_assistant_datasets.plugins.pytest_synthetic_home"]

PYTEST_INI = """
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
"""

INVENTORY = """
---
areas:
  - name: Kitchen
    id: kitchen
    floor: Ground
devices:
  - name: Kitchen Light
    id: kitchen_light
    area: kitchen
    info:
      model: Smart LED Bulb
      manufacturer: Philips
      sw_version: 1.2.3
entities:
  - name: Kitchen Light
    id: light.kitchen_light
    area: kitchen
    device: kitchen_light
    attributes:
      supported_color_modes:
        - brightness
      color_mode: brightness
      brightness: 100
"""


TEST_FILE_CONTENTS_FORMAT = f"""
from collections.abc import Generator
import datetime

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.util import dt as dt_util


@pytest.fixture(name="synthetic_home_yaml")
def synthetic_home_yaml_fixture() -> str:
    return \"\"\"{INVENTORY}\"\"\"



@pytest.fixture(name="expected_lingering_tasks")
def expected_lingering_tasks_fixtures() -> bool:
    return True


@pytest.fixture(name="expected_lingering_timers")
def expected_lingering_timers_fixtures() -> bool:
    return True


@pytest.fixture(autouse=True)
def restore_tz() -> Generator[None, None, None]:
    yield
    dt_util.set_default_time_zone(datetime.UTC)


def test_success(hass: HomeAssistant, synthetic_home_config_entry: ConfigEntry) -> None:
    assert synthetic_home_config_entry.state is ConfigEntryState.LOADED

    state = hass.states.get("light.kitchen_light")
    assert state
    assert state.state
"""


def test_synthetic_home_fixture(pytester: Any) -> None:
    """Exercise the report plugin."""

    pytester.makepyfile(TEST_FILE_CONTENTS_FORMAT)
    pytester.makeini(PYTEST_INI)

    result = pytester.runpytest(plugins=PLUGINS)
    stdout = "\n".join(result.stdout.lines)
    assert "1 passed" in stdout
