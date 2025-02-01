"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

import asyncio
from collections.abc import Callable, Awaitable
import logging
import uuid
import dataclasses
from typing import Any, cast
import enum
import json

import pytest
import yaml
from pyrate_limiter import Limiter

from homeassistant.core import HomeAssistant, Context
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, llm
from homeassistant.components.conversation import trace

from home_assistant_datasets.fixtures import ConversationAgent, EvalRecordWriter
from home_assistant_datasets.data_model import ModelConfig

from .data_model import (
    EvalTask,
    EntityState,
    ModelOutput,
)

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 40
MAX_TRIES = 3


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
            assert state
            assert state.state
            assert state.attributes
            results[entity_entry.entity_id] = EntityState(
                state=state.state, attributes=dict(state.attributes)
            )
            assert state.state not in (
                "unavailable",
                "unknown",
            ), f"Entity id has unavailable state {entity_entry.entity_id}: {state.state}"

        return results

    return func


def compare_state(v: Any, other_v: Any) -> bool:
    """Compare values for equivalence."""
    # Coerce some equivalent types for simpler comparisons
    if isinstance(v, tuple) or isinstance(other_v, tuple):
        v = list(v)
        other_v = list(v)
        return cast(bool, v == other_v)

    if isinstance(v, enum.StrEnum) or isinstance(other_v, enum.StrEnum):
        v = str(v)
        other_v = str(other_v)
        return cast(bool, v == other_v)

    if v == other_v:
        return True

    if str(v) == str(other_v):
        return True

    return False


def compute_entity_diff(
    a_state: EntityState, b_state: EntityState, ignored: set[str]
) -> dict[str, Any] | None:
    """Compute a diff between two entity states."""
    a = a_state.as_dict()
    b = b_state.as_dict()

    diff_attributes = set([])
    for k, v in a.items():
        other_v = b.get(k)
        if not compare_state(other_v, v):
            diff_attributes.add(k)
    for k in b:
        if k not in a and k:
            diff_attributes.add(k)
    diff_attributes = set({k for k in diff_attributes if k not in ignored})
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
        for entity_id, entity_state in (task.expect_changes or {}).items():
            if entity_id not in states:
                raise ValueError(
                    f"Entity defined in eval task does not exist: {entity_id}"
                )
            if entity_state.state is not None:
                states[entity_id].state = entity_state.state
            if entity_state.attributes is not None:
                if states[entity_id].attributes is None:
                    states[entity_id].attributes = {}
                states[entity_id].attributes = {
                    **states[entity_id].attributes,  # type: ignore[dict-item]
                    **entity_state.attributes,
                }

        for entity_id in updated_states:
            if entity_id not in states:
                raise ValueError(f"Unexpected new entity found: {entity_id}")

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
        return diffs

    return func


def dump_conversation_trace(trace: trace.ConversationTrace) -> list[dict[str, Any]]:
    """Serialize the conversation trace for evaluation."""
    trace_data = trace.as_dict()
    trace_events = trace_data["events"]
    result = []
    for trace_event in trace_events:
        trace_event_data = trace_event["data"]
        data = {}
        for k, v in trace_event_data.items():
            if isinstance(v, Context):
                v = dict(v.as_dict())
            if isinstance(v, list) and v and isinstance(v[0], llm.Tool):
                v = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": str(tool.parameters),
                    }
                    for tool in v
                ]
            data[k] = v
        result.append(
            {
                "event_type": str(trace_event["event_type"]),
                "data": data,
            }
        )
    return result


@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.parametrize("expected_lingering_tasks", [True])
async def test_assist_actions(
    hass: HomeAssistant,
    agent: ConversationAgent,
    eval_record_writer: EvalRecordWriter,
    model_config: ModelConfig,
    synthetic_home_config_entry: ConfigEntry,
    eval_task: EvalTask,
    get_state: Callable[[], dict[str, EntityState]],
    verify_state: Callable[
        [EvalTask, dict[str, EntityState], dict[str, EntityState]],
        Awaitable[dict[str, Any]],
    ],
    caplog: pytest.LogCaptureFixture,
    rate_limiter: Limiter,
) -> None:
    """Collects model responses for assist actions."""
    if rate_limiter:
        rate_limiter.try_acquire('item')

    yaml.SafeDumper.add_multi_representer(
        enum.StrEnum,
        yaml.representer.SafeRepresenter.represent_str,
    )

    states = get_state()

    # Run the conversation agent
    text = eval_task.input_text
    _LOGGER.debug("Prompt: %s", text)
    tries = 0
    response = ""
    retryable = True
    while tries < MAX_TRIES and retryable:
        retryable = False
        try:
            async with asyncio.timeout(TIMEOUT):
                response = await agent.async_process(hass, text)
        except (HomeAssistantError, TypeError, json.JSONDecodeError) as err:
            response = str(err)
        except (TimeoutError, asyncio.CancelledError):
            _LOGGER.debug("Timeout error (tries=%s)", tries)
            response = f"Timeout (after {tries} tries)"
            tries = tries + 1
            retryable = True
        await hass.async_block_till_done()
        _LOGGER.debug("Response: %s", response)

    updated_states = get_state()
    unexpected_states: dict[str, Any] | str
    try:
        unexpected_states = await verify_state(eval_task, states, updated_states)
    except ValueError as err:
        unexpected_states = f"Error verifying state: {err}"

    conversation_trace = []
    if (traces := trace.async_get_traces()) and (last_trace := traces[-1]):
        conversation_trace = dump_conversation_trace(last_trace)

    output = ModelOutput(
        uuid=str(uuid.uuid4()),  # Unique based on the model evaluated
        task_id=eval_task.task_id,
        category=eval_task.category,
        task={
            "input_text": eval_task.input_text,
            "expect_changes": {
                k: dataclasses.asdict(v)
                for k, v in (eval_task.expect_changes or {}).items()
            },
        },
        response=response,
        context={
            "unexpected_states": unexpected_states,
            "conversation_trace": conversation_trace,
            # TODO: Would be useful to support something like --dump-states for fully examining states
            # "state": states,
            # "updated_states": updated_states,
            "tries": tries,
        },
    )
    _LOGGER.info(output)
    eval_record_writer.write(dataclasses.asdict(output))

    # assert not [
    #     record.levelname for record in caplog.records if record.levelname == "ERROR"
    # ]
