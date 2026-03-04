"""Test for the light on door blueprint.

See ../README.md for instructions on how to evaluation solutions.
"""

import asyncio
import datetime
from collections.abc import Callable, Generator

import pytest

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from pytest_homeassistant_custom_component.common import async_fire_time_changed

from home_assistant_datasets.blueprint import BlueprintContentStatus, BlueprintContent
from home_assistant_datasets.entity_state import EntityState


DOOR_ENTITY = "binary_sensor.pantry_door"
LIGHT_ENTITY = "light.pantry_light"

WAIT_TIMEOUT_SEC = 5.0

# The problem statement asks for a 5 minute timeout, so set 10 minutes to be generous
LIGHT_TIMEOUT = datetime.timedelta(minutes=10)
BLUEPRINT_INPUT = {
    "door_sensor": DOOR_ENTITY,
    "light_switch": {
        "entity_id": [LIGHT_ENTITY],
    },
}


@pytest.fixture
async def automation_config(blueprint_content: BlueprintContent) -> dict[str, any]:
    return {
        "alias": "Pantry light door",
        "use_blueprint": {
            "path": blueprint_content.filename,
            "input": BLUEPRINT_INPUT,
        },
    }


@pytest.fixture(name="light_state_change")
async def light_event_fixture(
    hass: HomeAssistant,
) -> Generator[asyncio.Event]:
    """A fixture for an event that fires when the light state changes."""
    event = asyncio.Event()

    @callback
    async def state_changed(_: datetime.datetime) -> None:
        event.set()

    unsub = async_track_state_change_event(hass, LIGHT_ENTITY, state_changed)
    yield event
    unsub()


@pytest.mark.eval_model_outputs(task_id="light_on_door")
async def test_blueprint_inputs(blueprint_content: BlueprintContent) -> None:
    """Test the blueprint inputs."""
    blueprint_content.validate_inputs_present(BLUEPRINT_INPUT.keys())


@pytest.mark.eval_model_outputs(task_id="light_on_door")
async def test_door_open(
    hass: HomeAssistant,
    automation: BlueprintContentStatus,
    get_state: Callable[[], dict[str, EntityState]],
    light_state_change: asyncio.Event,
) -> None:
    """Test the light is controlled by opening the door."""
    automation.assert_valid()
    states = get_state()
    assert states.get(DOOR_ENTITY) == "off"
    assert states.get(LIGHT_ENTITY) == "off"

    assert not light_state_change.is_set()

    # Open the door and wait for the light to turn on
    hass.states.async_set(DOOR_ENTITY, "on")
    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await light_state_change.wait()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for light to turn on") from err

    expected_states = {**states, DOOR_ENTITY: "on", LIGHT_ENTITY: "on"}
    assert get_state() == expected_states


@pytest.mark.eval_model_outputs(task_id="light_on_door")
async def test_door_open_close(
    hass: HomeAssistant,
    automation: BlueprintContentStatus,
    get_state: Callable[[], dict[str, EntityState]],
    light_state_change: asyncio.Event,
) -> None:
    """Test the light is controlled by opening and closing the door."""
    automation.assert_valid()
    states = get_state()
    assert states.get(DOOR_ENTITY) == "off"
    assert states.get(LIGHT_ENTITY) == "off"

    assert not light_state_change.is_set()

    # Open the door and wait for the light to turn on
    hass.states.async_set(DOOR_ENTITY, "on")
    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await light_state_change.wait()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for light to turn on") from err

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

    expected_states = {**states, DOOR_ENTITY: "off", LIGHT_ENTITY: "off"}
    assert get_state() == expected_states


@pytest.mark.eval_model_outputs(task_id="light_on_door")
async def test_light_timeout(
    hass: HomeAssistant,
    automation: BlueprintContentStatus,
    get_state: Callable[[], dict[str, EntityState]],
    light_state_change: asyncio.Event,
) -> None:
    """Test the light is controlled by opening and closing the door."""
    automation.assert_valid()
    states = get_state()
    assert states.get(DOOR_ENTITY) == "off"
    assert states.get(LIGHT_ENTITY) == "off"

    assert not light_state_change.is_set()

    # Open the door and wait for the light to turn on
    hass.states.async_set(DOOR_ENTITY, "on")
    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await light_state_change.wait()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for light to turn on") from err

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

    # Verify the light has turned off even though the door is still open
    expected_states = {**states, DOOR_ENTITY: "on", LIGHT_ENTITY: "off"}
    assert get_state() == expected_states
