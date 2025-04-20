"""Test for the vacuum pause blueprint.

See ../README.md for instructions on how to evaluation solutions.
"""

import asyncio
import datetime
from collections.abc import Callable, Generator

import pytest

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event


from home_assistant_datasets.blueprint import BlueprintContentStatus, BlueprintContent
from home_assistant_datasets.entity_state import EntityState


VACUUM_ENTITY = "vacuum.vacuum_cleaner"
BIANRY_SENSOR_ENTITY = (
    "binary_sensor.rooftop_terrace_motion_sensor"  # Use the motion sensor as a trigger
)

WAIT_TIMEOUT_SEC = 5.0
BLUEPRINT_INPUT = {
    "phone_call_sensor": BIANRY_SENSOR_ENTITY,
    "vacuum_entity": VACUUM_ENTITY,
}


@pytest.fixture
async def automation_config(blueprint_content: BlueprintContent) -> dict[str, any]:
    return {
        "alias": "Vacuum Pause during phone call",
        "use_blueprint": {
            "path": blueprint_content.filename,
            "input": BLUEPRINT_INPUT,
        },
    }


@pytest.fixture(name="vacuum_state_change")
async def vacuum_event_fixture(
    hass: HomeAssistant,
) -> Generator[asyncio.Event]:
    """A fixture for an event that fires when the vacuum state changes."""
    event = asyncio.Event()

    @callback
    async def state_changed(_: datetime.datetime) -> None:
        event.set()

    unsub = async_track_state_change_event(hass, VACUUM_ENTITY, state_changed)
    yield event
    unsub()


@pytest.mark.eval_model_outputs(task_id="vacuum_pause")
async def test_blueprint_inputs(blueprint_content: BlueprintContent) -> None:
    """Test the blueprint inputs."""
    blueprint_content.validate_inputs_present(BLUEPRINT_INPUT.keys())


@pytest.mark.eval_model_outputs(task_id="vacuum_pause")
async def test_vacuum_running_and_paused(
    hass: HomeAssistant,
    automation: BlueprintContentStatus,
    get_state: Callable[[], dict[str, EntityState]],
    vacuum_state_change: asyncio.Event,
) -> None:
    """Test the vacuum is running then paused when the sensor fires."""
    automation.assert_valid()

    # Put vacuum in running state
    await hass.services.async_call(
        "vacuum",
        "start",
        service_data={"entity_id": VACUUM_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()

    states = get_state()
    assert states.get(VACUUM_ENTITY) == "cleaning"
    assert states.get(BIANRY_SENSOR_ENTITY) == "off"

    assert vacuum_state_change.is_set()
    vacuum_state_change.clear()

    # A phone call is received
    hass.states.async_set(BIANRY_SENSOR_ENTITY, "on")
    await asyncio.sleep(1e-5)  # Yield to allow the automation to run

    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await vacuum_state_change.wait()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for vacuum to pause") from err

    expected_states = {**states, VACUUM_ENTITY: "paused", BIANRY_SENSOR_ENTITY: "on"}
    assert get_state() == expected_states


@pytest.mark.eval_model_outputs(task_id="vacuum_pause")
async def test_vacuum_not_changed_when_idle(
    hass: HomeAssistant,
    automation: BlueprintContentStatus,
    get_state: Callable[[], dict[str, EntityState]],
    vacuum_state_change: asyncio.Event,
) -> None:
    """Test the vacuum is not paused when already idle."""
    automation.assert_valid()

    states = get_state()
    assert states.get(VACUUM_ENTITY) == "docked"
    assert states.get(BIANRY_SENSOR_ENTITY) == "off"

    assert not vacuum_state_change.is_set()

    # A phone call is received
    hass.states.async_set(BIANRY_SENSOR_ENTITY, "on")
    await asyncio.sleep(1e-5)  # Yield to allow the automation to run

    # Vacuum is still off, not paused
    expected_states = {**states, BIANRY_SENSOR_ENTITY: "on"}
    assert get_state() == expected_states
