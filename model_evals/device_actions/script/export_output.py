"""Device action offline evaluation metrics."""

from dataclasses import dataclass
from typing import Any

import json
import argparse
from itertools import islice
import logging
from operator import itemgetter
import pathlib
import sys
import yaml

from synthetic_home.device_types import DeviceState
from mashumaro import DataClassDictMixin
from mashumaro.codecs.yaml import yaml_decode

_LOGGER = logging.getLogger(__name__)


@dataclass
class DeviceState(DataClassDictMixin):
    """Information needed to set the synthetic state for an evaluation task."""

    name: str
    """Device name found in the synthetic home."""

    area: str
    """Device area found in the synthetic home."""

    state: str
    """The state to set on the device."""


@dataclass
class EvalTask(DataClassDictMixin):
    """Flattened detail about the task that is being evaluated."""

    home_id: str
    """Identifier for the synethetic home."""

    input_text: str
    """The conversation input text to state."""

    device_states: list[DeviceState]
    """The device state details to set as the start of the task."""


@dataclass
class Output(DataClassDictMixin):
    uuid: str
    task_id: str
    task: EvalTask
    response: str
    context: dict[str, Any]


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = argparse.ArgumentParser(description="Synthetic Home Evaluation Driver")
    parser.add_argument(
        "--log-level",
        default="warning",
        choices=["debug", "info", "warning", "error", "critical"],
        help="The log level",
    )
    parser.add_argument(
        "--model_outputs",
        type=str,
        help="The directory containing model outputs.",
        required=True,
    )
    parser.add_argument(
        "--output_type",
        type=str,
        help="The directory containing model outputs.",
        required=True,
    )
    return parser.parse_args()


def find_llm_call(trace: dict[str, Any]) -> dict[str, Any] | None:
    """Gets the llm call."""
    events = trace.get("events", [])
    for event in events:
        if event["event_type"] == "llm_tool_call":
            data = event["data"]
            return {
                "tool_name": data.get("tool_name"),
                "tool_args": data.get("tool_args"),
            }
    return None


def main():
    args = get_arguments()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    model_outputs = pathlib.Path(args.model_outputs)

    model_docs: dict[str, list[dict[str, str]]] = {}
    for model_output_file in model_outputs.glob("*.yaml"):
        documents = yaml.load_all(model_output_file.read_text(), Loader=yaml.Loader)
        for document in documents:
            output = Output(**document)

            tool_call = find_llm_call(output.context.get("conversation_trace", {}))
            if states := output.task.get("device_states"):
                device_state = DeviceState(**states[0])
                device_context = {"name": device_state.name, "area": device_state.area}
            else:
                device_context = {}

            simple_output = {
                "uuid": output.uuid,
                "task_id": output.task_id,
                "input": output.task["input_text"],
                "device_context": device_context,
                "tool_call": tool_call,
                "response": output.response,
            }
            if args.output_type == "json":
                print(json.dumps({"text": json.dumps(simple_output, indent=2)}))
            elif args.output_type == "yaml":
                print(yaml.dump(simple_output, sort_keys=False, explicit_start=True))
            else:
                raise ValueError("Invalid --output_type not 'json' or 'yaml'")


if __name__ == "__main__":
    main()
