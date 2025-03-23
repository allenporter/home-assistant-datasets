"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

import asyncio
import dataclasses
import datetime
import json
import logging
import uuid
import textwrap

import pytest
from pyrate_limiter import Limiter

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.conversation import trace

from home_assistant_datasets.fixtures import ConversationAgent, EvalRecordWriter
from home_assistant_datasets.data_model import ModelConfig

from home_assistant_datasets.tool.data_model import (
    EvalTask,
    ModelOutput,
)
from home_assistant_datasets.tool.fixtures import dump_conversation_trace

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
    eval_record_writer: EvalRecordWriter,
    model_config: ModelConfig,
    synthetic_home_config_entry: ConfigEntry,
    eval_task: EvalTask,
    rate_limiter: Limiter,
) -> None:
    """Collects model responses for automation actions."""
    if rate_limiter:
        rate_limiter.try_acquire("item")

    # Run the conversation agent
    text = eval_task.input_text
    _LOGGER.debug("Prompt: %s", text)
    tries = 0
    response = ""
    retryable = True
    duration: datetime.timedelta | None = None
    while tries < MAX_TRIES and retryable:
        retryable = False
        try:
            async with asyncio.timeout(TIMEOUT):
                start = datetime.datetime.now()
                response = await agent.async_process(hass, text)
                duration = datetime.datetime.now() - start
        except (HomeAssistantError, TypeError, json.JSONDecodeError) as err:
            response = str(err)
        except (TimeoutError, asyncio.CancelledError):
            _LOGGER.debug("Timeout error (tries=%s)", tries)
            response = f"Timeout (after {tries} tries)"
            tries = tries + 1
            retryable = True
        await hass.async_block_till_done()
        _LOGGER.debug("Response: %s", response)

    conversation_trace = []
    if (traces := trace.async_get_traces()) and (last_trace := traces[-1]):
        conversation_trace = dump_conversation_trace(last_trace)
    extra_context = {}
    if duration:
        extra_context["duration_ms"] = duration / datetime.timedelta(milliseconds=1)

    output = ModelOutput(
        uuid=str(uuid.uuid4()),  # Unique based on the model evaluated
        task_id=eval_task.task_id,
        category=eval_task.category,
        task={
            "input_text": eval_task.input_text,
        },
        response=response,
        context={
            "conversation_trace": conversation_trace,
            "tries": tries,
            **extra_context,
        },
    )
    _LOGGER.info(output)
    eval_record_writer.write(dataclasses.asdict(output))
