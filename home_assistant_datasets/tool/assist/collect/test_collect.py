"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

import dataclasses
import uuid
from typing import Any

import pytest

from homeassistant.core import HomeAssistant

from home_assistant_datasets.agent import ConversationAgent
from home_assistant_datasets.datasets.assist_eval_task import EvalTask
from home_assistant_datasets.entity_state.diff import EntityStateDiffFixture
from home_assistant_datasets.scrape import ModelOutput, ModelOutputWriter


# TODO: Some assist tests need to override validation to function
# @pytest.mark.parametrize("validate_entities", [None])
@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.parametrize("expected_lingering_tasks", [True])
async def test_assist_actions(
    hass: HomeAssistant,
    agent: ConversationAgent,
    model_id: str,
    model_output_writer: ModelOutputWriter,
    eval_task: EvalTask,
    entity_state_diff: EntityStateDiffFixture,
) -> None:
    """Collects model responses for assist actions."""
    task: dict[str, Any] = {"input_text": eval_task.input_text}
    if eval_task.action.expect_changes:
        task["expect_changes"] = {
            k: dataclasses.asdict(v)
            for k, v in (eval_task.action.expect_changes or {}).items()
        }
        entity_state_diff.prepare(
            eval_task.action.expect_changes or {}, eval_task.action.ignore_changes or {}
        )
    if eval_task.action.expect_response:
        task["expect_response"] = eval_task.action.expect_response
    if eval_task.action.expect_tool_call:
        task["expect_tool_call"] = eval_task.action.expect_tool_call

    # Run the conversation agent
    response = await agent.async_process(hass, eval_task.input_text)

    # Record the model output state
    context = {}
    if eval_task.action.expect_changes:
        context["unexpected_states"] = entity_state_diff.get_unexpected_changes()
    context.update(agent.trace_context())
    output = ModelOutput(
        uuid=str(uuid.uuid4()),  # Unique based on the model evaluated
        model_id=model_id,
        task_id=eval_task.task_id,
        category=eval_task.category,
        task=task,
        response=response,
        context=context,
    )
    model_output_writer.write(output)
