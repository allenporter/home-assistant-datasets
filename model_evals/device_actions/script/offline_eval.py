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
class Output(DataClassDictMixin):
    uuid: str
    task_id: str
    task: dict[str, Any]
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

COLUMNS = [
    "model_id",
    "label",
    "device_type",
    "text",
    "response",
    "tool_call",
    "entity_diff",
]


def print_yaml_row(row: dict[str, Any]) -> None:
    """Dump the record in yaml format."""
    print(yaml.dump(row, sort_keys=False, explicit_start=True))


def print_csv_row(row: dict[str, Any]) -> None:
    """Dump the record in csv format."""
    vals = []
    for col in COLUMNS:
        val = str(row[col])
        val = val.replace("\"", "'")
        vals.append(f"\"{val}\"")
    print(",".join(vals))



def main():
    args = get_arguments()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    model_outputs = pathlib.Path(args.model_outputs)


    if args.output_type == "csv":
        print(",".join(COLUMNS))
    print_row = print_csv_row if args.output_type == "csv" else print_yaml_row

    model_docs: dict[str, list[dict[str, str]]] = {}
    for model_output_file in model_outputs.glob("**/*.yaml"):
        stem = model_output_file.relative_to(model_outputs)
        filename = model_output_file.name[:-5] # strip .yaml
        model_id = str(list(stem.parents)[0])

        documents = yaml.load_all(model_output_file.read_text(), Loader=yaml.Loader)
        for document in documents:
            output = Output(**document)
            home_id = output.task["home_id"]
            device_type = filename[len(home_id)+1:]
            device_type = str(model_output_file.stem)[len(home_id)+1:]

            label = "Bad"
            unexpected_states = output.context["device_context"]["unexpected_states"]
            if len(unexpected_states) == 0:
                # Success!
                label = "Good"
                if "Sorry" in output.response:
                    raise ValueError(f"Incorrect expected states logic? Response said Sorry but no changes: {output.task_id}")

            tool_call = find_llm_call(output.context.get("conversation_trace", {}))

            simple_output = {
                "model_id": model_id,
                "label": label,
                "device_type": device_type,
                "text": output.task["input_text"],
                "response": output.response,
                "tool_call": tool_call,
                "entity_diff": str(unexpected_states)
            }
            print_row(simple_output)


if __name__ == "__main__":
    main()
