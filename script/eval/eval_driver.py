"""Driver that invokes home assistnat and pushes time forward."""

from dataclasses import dataclass, field
import logging
from mashumaro.codecs.yaml import yaml_decode
import os
import pathlib
import tqdm
import time
from slugify import slugify
from string import Template
import yaml

from homeassistant.core import HomeAssistant


_LOGGER = logging.getLogger(__name__)

EVAL_DIR = "eval"

# This is a copy of the system prompt we are evaluating.
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
Instructions: Check to make sure everything is normal at night
Summary: The bedroom is secure.

Area: Driveway
- Black Model 3 (Model 3)
  - binary_sensor Charging: off
  - sensor Battery level: 90%
  - sensor Battery range: 200 mi
  - binary_sensor Pedestrian Gate: off
  - switch Sprinkler: off
Instructions: Monitor the state of the car and the driveway.
Summary: The car is almost charged.

"""

AREA_SUMMARY_TEMPLATE = """

Here is the current state of all Areas. The user will ask you about one of these:

{%- for area in areas() %}
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
{%- endfor %}
"""

AREA_PROMPT = """
Area: {area_name}
Instructions: {instructions}
Summary:
"""


class DriverException(Exception):
    """Driver exception."""


def make_prompt(area_name: str, instructions: str) -> str:
    """Create a prompt for the agent to summarize the area."""
    return AREA_PROMPT.format(
        system_prompt=SYSTEM_PROMPT,
        area_name=area_name,
        instructions=instructions,
    )


@dataclass
class AreaEvaluationConfig:
    """Configuration for evaluating an area."""

    area: str
    """The name of the area."""

    instructions: list[str] = field(default_factory=list)
    """The instruction for the area."""


@dataclass
class EvaluationConfig:
    """Data about a synthetic home."""

    area_configs: list[AreaEvaluationConfig]


def load_evaluation_config(config_file: pathlib.Path) -> EvaluationConfig:
    """Load synthetic home configuration from disk."""
    try:
        with config_file.open("r") as f:
            content = f.read()
    except FileNotFoundError:
        raise DriverException(f"Configuration file '{config_file}' does not exist")
    try:
        return yaml_decode(content, EvaluationConfig)
    except ValueError as err:
        raise DriverException(f"Could not parse config file '{config_file}': {err}")


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
        eval_config_path: pathlib.Path,
        agent: ConversationAgent,
        output_dir: pathlib.Path,
    ) -> None:
        """Initialize the driver."""
        self._eval_config = load_evaluation_config(eval_config_path)
        if not self._eval_config.area_configs:
            raise DriverException("No area configurations found in evaluation config")
        self._agent = agent
        self._eval_dir = output_dir / EVAL_DIR / f"{time.time():.0f}"

    async def async_run(self, hass: HomeAssistant) -> bool:
        """Run an evaluation on the home conversation agent."""

        _LOGGER.info(
            "Loaded %s area summariies to evaluate", len(self._eval_config.area_configs)
        )
        os.makedirs(str(self._eval_dir), exist_ok=True)

        for area_config in tqdm.tqdm(self._eval_config.area_configs):
            _LOGGER.info(
                "Evaluating area summary: %s, %s",
                area_config.area,
                area_config.instructions,
            )
            prompt = make_prompt(area_config.area, ", ".join(area_config.instructions))
            _LOGGER.debug("Evaluating prompt: %s", prompt)

            response = await self._agent.async_process(hass, prompt)
            _LOGGER.debug("Response: %s", response)

            with open(self._eval_dir / f"{slugify(area_config.area)}.yaml", "w") as fd:
                fd.write(
                    yaml.dump(
                        {
                            "area": area_config.area,
                            "instructions": area_config.instructions,
                            "response": response,
                        }
                    )
                )

        _LOGGER.info(
            "Wrote %s summariies to %s",
            len(self._eval_config.area_configs),
            self._eval_dir,
        )

        return True
