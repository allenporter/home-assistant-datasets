"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

from collections.abc import Callable, Awaitable
import logging
import uuid
import dataclasses
from typing import Any

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.components.conversation import trace

from home_assistant_datasets.fixtures import ConversationAgent, EvalRecordWriter
from home_assistant_datasets.data_model import ModelConfig

from .data_model import (
    EvalTask,
    EntityState,
)

_LOGGER = logging.getLogger(__name__)


@pytest.fixture(name="get_state")
def get_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> Callable[[], dict[str, EntityState]]:
    """Fixture with a function call to change device state for evaluation."""

    def func() -> dict[str, EntityState]:
        entity_entries = er.async_entries_for_config_entry(
            entity_registry, synthetic_home_config_entry.entry_id
        )
        results = {}
        for entity_entry in entity_entries:
            state = hass.states.get(entity_entry.entity_id)
            results[entity_entry.entity_id] = EntityState(
                state=state.state, attributes=state.attributes
            )
        return results

    return func


def compute_entity_diff(
    a_state: EntityState, b_state: EntityState, ignored: set[str]
) -> dict[str, Any] | None:
    """Compute a diff between two entity states."""
    a = a_state.as_dict()
    b = b_state.as_dict()

    diff_attributes = set({})
    for k, v in a.items():
        if b.get(k) != v and k not in ignored:
            diff_attributes.add(k)
    for k in b:
        if k not in a and k not in ignored:
            diff_attributes.add(k)
    if not diff_attributes:
        return None
    return {
        "expected": {key: a.get(key) for key in diff_attributes},
        "got": {key: b.get(key) for key in diff_attributes},
    }


@pytest.fixture(name="verify_state")
async def verify_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> Callable[
    [EvalTask, dict[str, EntityState], dict[str, EntityState]],
    Awaitable[dict[str, Any]],
]:
    """Fixture that will verify the device state is in the expected state."""

    async def func(
        task: EvalTask,
        states: dict[str, EntityState],
        updated_states: dict[str, EntityState],
    ) -> dict[str, Any]:
        # Update states to what is expected
        for entity_id, entity_state in task.expect_changes.items():
            if entity_id not in states:
                return {
                    "unexpected_states": f"Entity defined in eval task does not exist: {entity_id}"
                }
            if entity_state.state is not None:
                states[entity_id].state = entity_state.state
            if entity_state.attributes is not None:
                if states[entity_id].attributes is None:
                    states[entity_id].attributes = {}
                states[entity_id].attributes = {
                    **states[entity_id].attributes,
                    **entity_state.attributes,
                }

        for entity_id in updated_states:
            if entity_id not in states:
                return {
                    "unexpected_states": f"Unexpected new entity found: {entity_id}"
                }

        diffs = {}
        for entity_id in states:
            ignored_attributes = (
                set(task.ignore_changes.get(entity_id, []))
                if task.ignore_changes
                else set({})
            )
            old = states[entity_id]
            new = updated_states[entity_id]
            if diff := compute_entity_diff(old, new, ignored_attributes):
                diffs[entity_id] = diff
        return {"unexpected_states": diffs}

    return func


@pytest.mark.parametrize("expected_lingering_timers", [True])
async def test_assist_actions(
    hass: HomeAssistant,
    agent: ConversationAgent,
    eval_record_writer: EvalRecordWriter,
    model_config: ModelConfig,
    synthetic_home_config_entry: ConfigEntry,
    eval_task: EvalTask,
    get_state: Callable[[], list[dict[str, dict[str, str]]]],
    verify_state: Callable[
        [EvalTask, dict[str, EntityState], dict[str, EntityState]],
        Awaitable[dict[str, Any]],
    ],
) -> None:
    """Collects model responses for assist actions."""

    # Setup the home for evaluation
    states = get_state()

    # Run the conversation agent
    text = eval_task.input_text
    _LOGGER.debug("Prompt: %s", text)
    try:
        response = await agent.async_process(hass, text)
    except (HomeAssistantError, TypeError) as err:
        response = str(err)
    await hass.async_block_till_done()
    _LOGGER.debug("Response: %s", response)

    updated_states = get_state()

    conversation_trace = {}
    if (traces := trace.async_get_traces()) and (last_trace := traces[-1]):
        conversation_trace = last_trace.as_dict()
    _LOGGER.debug("states=%s", states.get("light.kitchen_light"))
    _LOGGER.debug("updated_states=%s", updated_states.get("light.kitchen_light"))
    unexpected_states = await verify_state(eval_task, states, updated_states)

    eval_record_writer.write(
        {
            "uuid": str(uuid.uuid4()),  # Unique based on the model evaluated
            "task_id": eval_task.task_id,
            "task": {
                "input_text": eval_task.input_text,
                "expect_changes": {
                    k: dataclasses.asdict(v)
                    for k, v in (eval_task.expect_changes or {}).items()
                },
            },
            "response": response,
            "context": {
                "unexpected_states": unexpected_states,
                "conversation_trace": conversation_trace,
            },
        }
    )
