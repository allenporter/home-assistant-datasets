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


FAN_ENTITY = "fan.bathroom_exhaust_fan"
HUMIDITY_SENSOR_ENTITY = "sensor.bathroom_exhaust_fan_humidity"
FAN_TARGET_LEVEL = 65

WAIT_TIMEOUT_SEC = 5.0
BLUEPRINT_INPUT = {
    "fan_entity": FAN_ENTITY,
    "humidity_sensor": HUMIDITY_SENSOR_ENTITY,
    "humidity_level": FAN_TARGET_LEVEL,
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


@pytest.mark.eval_model_outputs(task_id="humidity_fan")
async def test_blueprint_inputs(blueprint_content: BlueprintContent) -> None:
    """Test the blueprint inputs."""
    blueprint_content.validate_inputs_present(BLUEPRINT_INPUT.keys())


@pytest.fixture(name="fan_state_changed")
async def fan_event_fixture(
    hass: HomeAssistant,
) -> Generator[asyncio.Event]:
    """A fixture for an event that fires when the fan state changes."""
    event = asyncio.Event()

    @callback
    async def state_changed(_: datetime.datetime) -> None:
        event.set()

    unsub = async_track_state_change_event(hass, FAN_ENTITY, state_changed)
    yield event
    unsub()


@pytest.mark.eval_model_outputs(task_id="humidity_fan")
async def test_fan_triggered_on(
    hass: HomeAssistant,
    automation: BlueprintContentStatus,
    get_state: Callable[[], dict[str, EntityState]],
    fan_state_changed: asyncio.Event,
) -> None:
    """Test the fan is turned on when the sensor reaches the target."""
    automation.assert_valid()

    states = get_state()
    assert states.get(FAN_ENTITY) == "off"
    assert states.get(HUMIDITY_SENSOR_ENTITY) == "45"

    assert not fan_state_changed.is_set()

    # The humidity goes about the target level
    hass.states.async_set(HUMIDITY_SENSOR_ENTITY, str(FAN_TARGET_LEVEL + 10))
    await asyncio.sleep(1e-5)  # Yield to allow the automation to run

    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await fan_state_changed.wait()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for fan state to change") from err

    expected_states = {**states, FAN_ENTITY: "on", HUMIDITY_SENSOR_ENTITY: "75"}
    assert get_state() == expected_states


@pytest.mark.eval_model_outputs(task_id="humidity_fan")
async def test_fan_triggered_off(
    hass: HomeAssistant,
    automation: BlueprintContentStatus,
    get_state: Callable[[], dict[str, EntityState]],
    fan_state_changed: asyncio.Event,
) -> None:
    """Test the fan is turned off when the sensor goes below the target."""
    automation.assert_valid()

    # Put fan in the running state
    await hass.services.async_call(
        "fan",
        "turn_on",
        service_data={"entity_id": FAN_ENTITY},
        blocking=True,
    )
    await hass.async_block_till_done()
    hass.states.async_set(HUMIDITY_SENSOR_ENTITY, str(FAN_TARGET_LEVEL + 10))

    states = get_state()
    assert states.get(FAN_ENTITY) == "on"
    assert states.get(HUMIDITY_SENSOR_ENTITY) == "75"

    assert fan_state_changed.is_set()
    fan_state_changed.clear()

    # The humidity goes below the target level
    hass.states.async_set(HUMIDITY_SENSOR_ENTITY, str(FAN_TARGET_LEVEL - 10))
    await asyncio.sleep(1e-5)  # Yield to allow the automation to run

    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await fan_state_changed.wait()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for fan state to change") from err

    expected_states = {**states, FAN_ENTITY: "off", HUMIDITY_SENSOR_ENTITY: "55"}
    assert get_state() == expected_states
