"""An evaluation for an Area Summary agent."""

from collections.abc import Generator
import logging
import os
import pathlib
from slugify import slugify
from typing import Any
from unittest.mock import patch, mock_open

import pytest
import pytest_socket
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import area_registry as ar
from homeassistant.setup import async_setup_component

from pytest_homeassistant_custom_component.common import MockConfigEntry

from home_assistant_datasets import secrets

from .conftest import ConversationAgent, EvalRecordWriter

from custom_components import synthetic_home  # Load synethic home
from custom_components import vicuna_conversation


_LOGGER = logging.getLogger(__name__)


AREA_SUMMARY_PROMPT = """
Please summarize the status of an area of the home. Your summaries are succint,
and do not mention boring details or things that seem very mundane or minor. A
one sentence summary is best.

Here is an example of the input and output:

Area: Bedroom 1
- Bedroom 1 Light (Dimmable Smart Bulb)
    light: off
- Smart Lock (Encode Smart WiFi Deadbolt)
    binary_sensor: off
    binary_sensor Tamper: off
    binary_sensor Battery: off
    sensor Battery: 90 %
Summary: The bedroom is secure.

Area: Driveway
- Black Model 3 (Model 3)
  - binary_sensor Charging: off
  - sensor Battery level: 90%
  - sensor Battery range: 200 mi
  - binary_sensor Pedestrian Gate: off
  - switch Sprinkler: off
Summary: The car is almost charged.

"""

AREA_PROMPT = """
{system_prompt}

Area: {area_name}
Summary:
"""


def make_prompt(area_name: str) -> str:
    """Create a prompt for the agent to summarize the area."""
    return AREA_PROMPT.format(
        system_prompt=AREA_SUMMARY_PROMPT,
        area_name=area_name,
    )


@pytest.fixture(name="conversation_agent_id")
async def mock_conversation_agent_id(
    conversation_agent_domain: str,
    openai_config_entry: MockConfigEntry,
    vicuna_conversation_config_entry: MockConfigEntry,
) -> str:
    """Return the id for the conversation agent under test."""
    if conversation_agent_domain == "openai_conversation":
        return openai_config_entry.entry_id
    if conversation_agent_domain == "vicuna_conversation":
        return vicuna_conversation_config_entry.entry_id
    raise ValueError(f"Conversation Agent domain not found: {conversation_agent_domain}")


@pytest.mark.parametrize(
    ("conversation_agent_domain"),
    [
        ("vicuna_conversation")
    ]
)
@pytest.mark.parametrize(
    ("synthetic_home_config"),
    [
        ("datasets/devices/home1-us.yaml"),
        ("datasets/devices/apartament4-pl.yaml"),
        ("datasets/devices/casa-adosada-en-la-costa-es.yaml"),
        ("datasets/devices/lakeside-retreat-de.yaml"),
    ],
)
async def test_areas(hass: HomeAssistant, agent: ConversationAgent, synthetic_home_config: str) -> None:
    """Evaluation that tests an area summary."""

    area_registry = ar.async_get(hass)
    area_names = [ area.name for area in area_registry.async_list_areas() ]
    _LOGGER.info("Loaded %s areas to evaluate", len(area_names))

    writer = EvalRecordWriter(pathlib.Path("out"), pathlib.Path(synthetic_home_config).name)
    await writer.open()

    for area_name in area_names:
        _LOGGER.info(
            "Evaluating area summary: %s",
            area_name,
        )
        prompt = make_prompt(area_name)
        _LOGGER.debug("Evaluating prompt: %s", prompt)

        response = await agent.async_process(hass, prompt)
        _LOGGER.debug("Response: %s", response)

        await writer.write(
            {
                "area": area_name,
                "response": response,
            }
        )

    await writer.close()
