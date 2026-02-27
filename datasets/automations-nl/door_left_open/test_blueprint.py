"""Test for the door left open blueprint

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

DOOR_ENTITY = "binary_sensor.entry_door"
MEDIA_PLAYER_ENTITY = "media_player.smart_speaker"

WAIT_TIMEOUT_SEC = 2.0

# The open duration below
OPEN_DURATION = datetime.timedelta(minutes=15)
BLUEPRINT_INPUT = {
    "door_sensor": DOOR_ENTITY,
    "alert_media": {
        "entity_id": MEDIA_PLAYER_ENTITY,
        "media_content_id": "media-source://tts/cloud?message=Door+Open",
        "media_content_type": "provider",
    },
    "open_duration": "00:15:00",
}


@pytest.fixture
async def automation_config(blueprint_content: BlueprintContent) -> dict[str, any]:
    return {
        "alias": "Door left open",
        "use_blueprint": {
            "path": blueprint_content.filename,
            "input": BLUEPRINT_INPUT,
        },
    }


@pytest.fixture(name="media_player_state_change")
async def media_player_state_changet_fixture(
    hass: HomeAssistant,
) -> Generator[asyncio.Event]:
    """A fixture for an event that fires when the media player state changes."""

    event = asyncio.Event()

    @callback
    async def state_changed(_: datetime.datetime) -> None:
        event.set()

    unsub = async_track_state_change_event(hass, MEDIA_PLAYER_ENTITY, state_changed)
    yield event
    unsub()


@pytest.mark.eval_model_outputs(task_id="door_left_open")
async def test_blueprint_inputs(blueprint_content: BlueprintContent) -> None:
    """Test the blueprint inputs."""
    blueprint_content.validate_inputs_present(BLUEPRINT_INPUT.keys())


@pytest.mark.eval_model_outputs(task_id="door_left_open")
async def test_door_open_plays_media(
    hass: HomeAssistant,
    automation: BlueprintContentStatus,
    get_state: Callable[[], dict[str, EntityState]],
    media_player_state_change: asyncio.Event,
) -> None:
    """Test the media is played when the door is left open."""
    automation.assert_valid()
    states = get_state()
    assert states.get(DOOR_ENTITY) == "off"
    assert states.get(MEDIA_PLAYER_ENTITY) == "off"
    assert not media_player_state_change.is_set()

    # Open the door and verify that no other states have changed.
    hass.states.async_set(DOOR_ENTITY, "on")
    await asyncio.sleep(0.01)

    expected_states = {**states, DOOR_ENTITY: "on"}
    assert get_state() == expected_states

    # The door has been left open for too long
    async_fire_time_changed(hass, datetime.datetime.now() + OPEN_DURATION)

    # Wait for the media player to start playing to turn off
    try:
        async with asyncio.timeout(WAIT_TIMEOUT_SEC):
            await media_player_state_change.wait()
            await hass.async_block_till_done()
    except TimeoutError as err:
        raise TimeoutError("Timeout waiting for media player state change") from err

    expected_states = {**states, DOOR_ENTITY: "on", MEDIA_PLAYER_ENTITY: "playing"}
    assert get_state() == expected_states
