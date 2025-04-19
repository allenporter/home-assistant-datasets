"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

import logging
import uuid
import textwrap

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from home_assistant_datasets.agent import ConversationAgent
from home_assistant_datasets.datasets.assist_eval_task import EvalTask
from home_assistant_datasets.scrape import ModelOutput, ModelOutputWriter

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 40
MAX_TRIES = 3


@pytest.fixture(name="system_prompt")
async def system_prompt_fixture() -> str:
    """Fixture to provide the system prompt or None to use the default."""
    return textwrap.dedent(
        """
        Create a Home Assistant blueprint YAML configuration based on the user request.

        Please respond only with markdown that contains yaml. You can
        add comments inline with your step by step thinking. The response must start
        with ```yaml and end with ``` because your answer will be parsed by code. It
        is very important to stick to the format.
        """
    )


@pytest.mark.parametrize("expected_lingering_timers", [True])
@pytest.mark.parametrize("expected_lingering_tasks", [True])
async def test_assist_actions(
    hass: HomeAssistant,
    agent: ConversationAgent,
    model_output_writer: ModelOutputWriter,
    synthetic_home_config_entry: ConfigEntry,
    eval_task: EvalTask,
) -> None:
    """Collects model responses for automation actions."""
    # Run the conversation agent
    response = await agent.async_process(hass, eval_task.input_text)

    output = ModelOutput(
        uuid=str(uuid.uuid4()),  # Unique based on the model evaluated
        task_id=eval_task.task_id,
        category=eval_task.category,
        task={
            "input_text": eval_task.input_text,
        },
        response=response,
        context=agent.trace_context(),
    )
    _LOGGER.info(output)
    model_output_writer.write(output)
