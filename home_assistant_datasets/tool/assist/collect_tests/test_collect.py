"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

import dataclasses
import enum
import logging
import uuid

import pytest
import yaml

from homeassistant.core import HomeAssistant

from home_assistant_datasets.agent import ConversationAgent
from home_assistant_datasets.datasets.assist_eval_task import EvalTask
from home_assistant_datasets.entity_state.diff import EntityStateDiffFixture
from home_assistant_datasets.scrape import ModelOutput, ModelOutputWriter

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 40
MAX_TRIES = 3


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
    yaml.SafeDumper.add_multi_representer(
        enum.StrEnum,
        yaml.representer.SafeRepresenter.represent_str,
    )
    entity_state_diff.prepare(
        eval_task.action.expect_changes or {}, eval_task.action.ignore_changes or {}
    )

    # Run the conversation agent
    response = await agent.async_process(hass, eval_task.input_text)

    unexpected_states = entity_state_diff.get_unexpected_changes()
    output = ModelOutput(
        uuid=str(uuid.uuid4()),  # Unique based on the model evaluated
        model_id=model_id,
        task_id=eval_task.task_id,
        category=eval_task.category,
        task={
            "input_text": eval_task.input_text,
            "expect_changes": {
                k: dataclasses.asdict(v)
                for k, v in (eval_task.action.expect_changes or {}).items()
            },
            "expect_response": eval_task.action.expect_response,
        },
        response=response,
        context={"unexpected_states": unexpected_states, **agent.trace_context()},
    )
    _LOGGER.info(output)
    model_output_writer.write(output)
