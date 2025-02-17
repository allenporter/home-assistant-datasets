"""Test for the light on door blueprint."""

import asyncio
import datetime
import pathlib
from collections.abc import Callable, Generator

import pytest

from homeassistant.core import HomeAssistant, callback
from homeassistant.setup import async_setup_component
from homeassistant.helpers.event import async_track_state_change_event

from pytest_homeassistant_custom_component.common import async_fire_time_changed

from home_assistant_datasets.tool.data_model import EntityState

PATH = pathlib.Path(__file__).parent
FIXTURES = PATH / "_fixtures.yaml"
SOLUTION = PATH / "_solution.yaml"
DOOR_ENTITY = "binary_sensor.pantry_door"
LIGHT_ENTITY = "light.pantry_light"
AUTOMATION_CONFIG = {
    "alias": "Pantry light door",
    "use_blueprint": {
        "path": str(SOLUTION),
        "input": {
            "door_sensor": DOOR_ENTITY,
            "light_switch": {
                "entity_id": [LIGHT_ENTITY],
            },
        },
    },
}
WAIT_TIMEOUT_SEC = 5.0

# The problem statement asks for a 5 minute timeout, so set 10 minutes to be generous
LIGHT_TIMEOUT = datetime.timedelta(minutes=10)


@pytest.fixture
def synthetic_home_yaml() -> str:
    """Fixture to load synthetic home entities."""
    return FIXTURES.read_text()


@pytest.fixture(autouse=True)
async def automation_fixture(hass: HomeAssistant) -> None:
    """Fixture to set up the blueprint."""
    assert await async_setup_component(
        hass, "automation", {"automation": [AUTOMATION_CONFIG]}
    )
    await hass.async_block_till_done()


@pytest.fixture(name="light_state_change")
async def light_event_fixture(hass: HomeAssistant) -> Generator[asyncio.Event]:
    """A fixture for an event that fires when the light state changes."""

    event = asyncio.Event()

    @callback
    async def state_changed(_: datetime.datetime) -> None:
        event.set()

    unsub = async_track_state_change_event(hass, LIGHT_ENTITY, state_changed)
    yield event
    unsub()


async def test_door_open(
    hass: HomeAssistant,
    get_state: Callable[[], dict[str, EntityState]],
    light_state_change: asyncio.Event,
) -> None:
    """Test the light is controlled by opening the door."""
    states = get_state()
    assert states.get(DOOR_ENTITY) == "off"
    assert states.get(LIGHT_ENTITY) == "off"

    assert not light_state_change.is_set()

    # Open the door
    hass.states.async_set(DOOR_ENTITY, "on")

    # Wait for the light to turn on
    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await light_state_change.wait()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for light to turn on") from err

    # Verify the automation has turned the light on
    expected_states = {**states, DOOR_ENTITY: "on", LIGHT_ENTITY: "on"}
    assert get_state() == expected_states

    # Yield to the automation to let it set up the idle timeout or turn off trigger.
    await asyncio.sleep(0.01)
    light_state_change.clear()


async def test_door_open_close(
    hass: HomeAssistant,
    get_state: Callable[[], dict[str, EntityState]],
    light_state_change: asyncio.Event,
) -> None:
    """Test the light is controlled by opening and closing the door."""
    states = get_state()
    assert states.get(DOOR_ENTITY) == "off"
    assert states.get(LIGHT_ENTITY) == "off"

    assert not light_state_change.is_set()

    # Open the door
    hass.states.async_set(DOOR_ENTITY, "on")

    # Wait for the light to turn on
    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await light_state_change.wait()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for light to turn on") from err

    # Verify the automation has turned the light on
    expected_states = {**states, DOOR_ENTITY: "on", LIGHT_ENTITY: "on"}
    assert get_state() == expected_states

    # Yield to the automation to let it set up the idle timeout or turn off trigger.
    await asyncio.sleep(0.01)
    light_state_change.clear()

    # After 30 seconds the door closes. We expect the light to also turn off.
    async_fire_time_changed(
        hass, datetime.datetime.now() + datetime.timedelta(seconds=30)
    )
    hass.states.async_set(DOOR_ENTITY, "off")

    # Wait for the light to turn off
    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await light_state_change.wait()
            await hass.async_block_till_done()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for light to turn off") from err

    # Verify the light has turned off
    expected_states = {**states, DOOR_ENTITY: "off", LIGHT_ENTITY: "off"}
    assert get_state() == expected_states


async def test_light_timeout(
    hass: HomeAssistant,
    get_state: Callable[[], dict[str, EntityState]],
    light_state_change: asyncio.Event,
) -> None:
    """Test the light is controlled by opening and closing the door."""
    states = get_state()
    assert states.get(DOOR_ENTITY) == "off"
    assert states.get(LIGHT_ENTITY) == "off"

    assert not light_state_change.is_set()

    # Open the door
    hass.states.async_set(DOOR_ENTITY, "on")

    # Wait for the light to turn on
    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await light_state_change.wait()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for light to turn on") from err

    # Verify the automation has turned the light on
    expected_states = {**states, DOOR_ENTITY: "on", LIGHT_ENTITY: "on"}
    assert get_state() == expected_states

    # Yield to the automation to let it set up the idle timeout or turn off trigger.
    await asyncio.sleep(0.01)
    light_state_change.clear()

    # Wait for some timeout and verify the light has been automatically turned off.
    async_fire_time_changed(hass, datetime.datetime.now() + LIGHT_TIMEOUT)
    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await light_state_change.wait()
            await hass.async_block_till_done()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for light to turn off") from err

    # Verify the light has turned off
    expected_states = {**states, DOOR_ENTITY: "off", LIGHT_ENTITY: "off"}
    assert get_state() == expected_states
