"""Driver that invokes home assistnat and pushes time forward."""

from importlib import resources
import logging
import pathlib
from string import Template
import yaml
import tqdm

from homeassistant.core import HomeAssistant
from homeassistant import bootstrap, config as conf_util, setup
from homeassistant.config_entries import ConfigEntryState


_LOGGER = logging.getLogger(__name__)

STORAGE_RESOURCE_PATH = resources.files().joinpath("storage")
DEST_STORAGE_DIR = ".storage"

SYSTEM_PROMPT = """
You are an agent running in Home Assistant. Your job is to summarize the status of an area
which will be fed as input into other agents. The user will feed in details about
areas and devices in the home, and you will respond with a summary of the status of the area.

Your summaries are succint, and do not mention boring details or things that seem
very mundane or minor. A one sentence summary is best.

Here is an example of the input and output:

Area: Bedroom 1
- Bedroom 1 Light (Dimmable Smart Bulb)
    light: off
- Smart Lock (Encode Smart WiFi Deadbolt)
    binary_sensor: off
    binary_sensor Tamper: off
    binary_sensor Battery: off
    sensor Battery: 90 %
Instruction: Check to make sure everything is normal at night
Summary: The bedroom is secure.

Area: Driveway
- Black Model 3 (Model 3)
  - binary_sensor Charging: off
  - sensor Battery level: 90%
  - sensor Battery range: 200 mi
  - binary_sensor Pedestrian Gate: off
  - switch Sprinkler: off
Instruction: Monitor the state of the car and the driveway.
Summary: The car is almost charged.
"""

SET_AREA_VARIABLE = """{%- set area = "$area" %}"""
AREA_SUMMARY_TEMPLATE = """
Area: {{ area }}
  {%- for device in area_devices(area) -%}
    {%- if not device_attr(device, "disabled_by") and not device_attr(device, "entry_type") and device_attr(device, "name") %}
        {%- set device_name = device_attr(device, "name_by_user") | default(device_attr(device, "name"), True) %}

- {{ device_name  }}{% if device_attr(device, "model") and (device_attr(device, "model") | string) not in (device_attr(device, "name") | string) %} ({{ device_attr(device, "model") }}){% endif %}
      {%- set entity_info = namespace(printed=false) %}
      {%- for entity_id in device_entities(device) -%}
        {%- set entity_name = state_attr(entity_id, "friendly_name") | replace(device_name, "") | trim %}
    {{ entity_id.split(".")[0] -}}
        {%- if entity_name %} {{ entity_name }}{% endif -%}
        : {{ states(entity_id, rounded=True, with_unit=True) }}
      {%- endfor %}
    {%- endif %}
  {%- endfor %}
"""

AREA_PROMPT = """
{system_prompt}

The user will enter an area with an instruction below and you will respond with a summary of the area.

{set_area_variable}
{area_summary_template}
Instruction: {instruction}
Summary:
"""


def make_prompt(area_name: str, instruction: str) -> str:
    """Create a prompt for the agent to summarize the area."""
    set_area_var = Template(SET_AREA_VARIABLE).substitute(area=area_name)
    return AREA_PROMPT.format(
        system_prompt=SYSTEM_PROMPT,
        set_area_variable=set_area_var,
        area_summary_template=AREA_SUMMARY_TEMPLATE,
        instruction=instruction,
    )


class DriverException(Exception):
    """Driver exception."""


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


class EvalDriver:
    """Driver that performs service calls and evaluates the results."""

    def __init__(
        self,
        synthetic_home_config: pathlib.Path,
        agent: ConversationAgent,
    ) -> None:
        """Initialize the driver."""
        self._synthetic_home_config = synthetic_home_config
        self._agent = agent

    async def async_run(self, hass: HomeAssistant) -> bool:
        """Run an evaluation on the home conversation agent."""
        with open(
            pathlib.Path(hass.config.config_dir) / self._synthetic_home_config, "r"
        ) as fd:
            content = fd.read()

        obj = yaml.load(content, Loader=yaml.FullLoader)
        summaries = obj.get("summaries")
        if not summaries:
            raise DriverException("No summaries found in configuration")

        area_summaries = summaries.get("area_summaries")
        if not area_summaries:
            raise DriverException("No area summaries found in configuration")

        _LOGGER.info("Loaded %s area summariies to evaluate", len(area_summaries))

        for area_summary in tqdm.tqdm(area_summaries):
            _LOGGER.info("Evaluating area summary: %s", area_summary)
            prompt = make_prompt(area_summary, area_summary)
            _LOGGER.debug("Evaluating prompt: %s", prompt)

            summary = await self._agent.async_process(hass, prompt)
            _LOGGER.info("Response: %s", summary)

        return True
