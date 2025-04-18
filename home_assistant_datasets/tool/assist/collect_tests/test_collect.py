"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

from collections.abc import Callable, Awaitable
import dataclasses
import enum
import logging
from typing import Any
import uuid

import pytest
import yaml

from homeassistant.core import HomeAssistant

from home_assistant_datasets.agent import ConversationAgent
from home_assistant_datasets.fixtures import EvalRecordWriter
from home_assistant_datasets.tool.data_model import (
    EvalTask,
    EntityState,
    ModelOutput,
)

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 40
MAX_TRIES = 3


@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.parametrize("expected_lingering_tasks", [True])
async def test_assist_actions(
    hass: HomeAssistant,
    agent: ConversationAgent,
    eval_record_writer: EvalRecordWriter,
    eval_task: EvalTask,
    get_state: Callable[[], dict[str, EntityState]],
    verify_state: Callable[
        [EvalTask, dict[str, EntityState], dict[str, EntityState]],
        Awaitable[dict[str, Any]],
    ],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Collects model responses for assist actions."""
    yaml.SafeDumper.add_multi_representer(
        enum.StrEnum,
        yaml.representer.SafeRepresenter.represent_str,
    )

    states = get_state()

    # Run the conversation agent
    response = await agent.async_process(hass, eval_task.input_text)

    updated_states = get_state()
    unexpected_states: dict[str, Any] | str
    try:
        unexpected_states = await verify_state(eval_task, states, updated_states)
    except ValueError as err:
        unexpected_states = f"Error verifying state: {err}"

    context = agent.trace_context()
    context["unexpected_states"] = unexpected_states

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
            "expect_response": eval_task.expect_response,
        },
        response=response,
        context=context,
    )
    _LOGGER.info(output)
    eval_record_writer.write(dataclasses.asdict(output))
