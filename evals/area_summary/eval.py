"""The Area Summary evaluation."""

from dataclasses import dataclass
import logging
import pathlib
import os
from slugify import slugify
from typing import Any


import tqdm
import yaml

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

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


class ConversationAgent:
    """A client library for a conversation agent service call."""

    def __init__(self, agent_id: str) -> None:
        """Initialize the agent."""
        self._agent_id = agent_id

    async def async_process(self, hass: HomeAssistant, text: str) -> str:
        """Process a text input and return the response."""
        service_response = await hass.services.async_call(
            "conversation",
            "process",
            {"agent_id": self._agent_id, "text": text},
            blocking=True,
            return_response=True,
        )
        response = service_response["response"]
        return response["speech"]["plain"]["speech"]



async def async_run_eval(hass: HomeAssistant, config: dict[str, Any]) -> None:
    """Run the evaluation."""

    eval_dir = pathlib.Path(config["eval_dir"])
    os.makedirs(eval_dir, exist_ok=True)

    # Find the conversation agent id to evaluate based on the domain in the config file
    config_entry_ids = [ entry.entry_id for entry in hass.config_entries.async_entries() if entry.domain in config["conversation_agent_domain"] ]
    if len(config_entry_ids) > 1:
        raise ValueError("Found more than one config entry for domain {config['convesation_agent_domain']}")
    if not config_entry_ids:
        raise ValueError("Found no config entry for domain {config['convesation_agent_domain']}")
    conversation_agent_id = config_entry_ids[0]

    agent = ConversationAgent(conversation_agent_id)

    area_registry = ar.async_get(hass)
    area_names = [ area.name for area in area_registry.async_list_areas() ]

    _LOGGER.info("Loaded %s areas to evaluate", len(area_names))

    for area_name in tqdm.tqdm(area_names):
        _LOGGER.info(
            "Evaluating area summary: %s",
            area_name,
        )
        prompt = make_prompt(area_name)
        _LOGGER.debug("Evaluating prompt: %s", prompt)

        response = await agent.async_process(hass, prompt)
        _LOGGER.debug("Response: %s", response)

        with open(eval_dir / f"{slugify(area_name)}.yaml", "w") as fd:
            fd.write(
                yaml.dump(
                    {
                        "area": area_name,
                        "response": response,
                    }
                )
            )

    _LOGGER.info(
        "Wrote %s summariies to %s",
        len(area_names),
        eval_dir,
    )
