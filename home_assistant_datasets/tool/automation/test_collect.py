"""An evaluation for calling Device Actions, expected to be used to evaluate intents."""

import textwrap
import asyncio
import logging
import uuid
import dataclasses
import json

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
from home_assistant_datasets.tool.conftest import dump_conversation_trace

_LOGGER = logging.getLogger(__name__)
TIMEOUT = 40
MAX_TRIES = 3


@pytest.fixture(name="system_prompt")
async def system_prompt_fixture(eval_task: EvalTask) -> str:
    """Fixture to provide the system prompt or None to use the default."""
    return textwrap.dedent(
        """
        Create a Home Assistant automation YAML configuration based on the following
        user request.

        An example automation such as "When Paulus arrives home and it is after sunset: Turn the lights on in the living room."
        will be broken up into these parts:

        (trigger)    When Paulus arrives home
        (condition)  and it is after sunset:
        (action)     Turn the lights on in the living room

        The first part is the trigger of the automation rule. Triggers describe events that should trigger the automation rule. In this case, it is a person arriving home, which can be observed in Home Assistant using devices/sensors by observing the state of Paulus changing from not_home to home.
        The second part is the condition. Conditions are optional tests that can limit an automation rule to only work in your specific use cases. A condition will test against the current state of the system. This includes the current time, devices, people and other things like the sun. In this case, we only want to act when the sun has set.
        The third part is the action, which will be performed when a rule is triggered and all conditions are met. For example, it can turn a light on, set the temperature on your thermostat or activate a scene.

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

    conversation_trace = []
    if (traces := trace.async_get_traces()) and (last_trace := traces[-1]):
        conversation_trace = dump_conversation_trace(last_trace)

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
        },
    )
    _LOGGER.info(output)
    eval_record_writer.write(dataclasses.asdict(output))
