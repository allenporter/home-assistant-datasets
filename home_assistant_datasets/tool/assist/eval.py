"""Evaluate data collected from the home assistant conversation agent.

See `assist_collect` for the step to collect data. You can then run an offline
analysis of the model using the following command:

```bash
$ OUTPUT_DIR="output/$(date +"%Y-%m-%d")/"
$ home-assistant-datasets assist_eval --model_output_dir=${OUTPUT_DIR}
```

"""

import argparse
import logging
import pathlib
from typing import Any
from dataclasses import dataclass

import yaml
from mashumaro import DataClassDictMixin
from mashumaro.codecs.yaml import yaml_decode

from homeassistant.components.conversation import trace

from .data_model import ModelOutput


_LOGGER = logging.getLogger(__name__)



def find_llm_call(trace_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Gets the llm call from the conversation trace."""
    tool_call = next(iter(event for event in trace_events if event["event_type"] == trace.ConversationTraceEventType.LLM_TOOL_CALL), None)
    if tool_call is None:
        return None

    data = tool_call["data"]
    return {
        "tool_name": data.get("tool_name"),
        "tool_args": data.get("tool_args"),
    }


COLUMNS = [
    "model_id",
    "task_prefix",
    "category",
    "label",
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



def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--model_output_dir",
        type=str,
        help="Specifies the model output directory from `collect`.",
    )
    args.add_argument(
        "--output_type",
        type=str,
        help="Specifies the output type.",
    )


def run(args: argparse.Namespace) -> int:

    model_outputs = pathlib.Path(args.model_output_dir)
    if args.output_type == "csv":
        print(",".join(COLUMNS))
    print_row = print_csv_row if args.output_type == "csv" else print_yaml_row
    print_diff = str if args.output_type == "csv" else dict

    model_docs: dict[str, list[dict[str, str]]] = {}
    for model_output_file in model_outputs.glob("**/*.yaml"):
        stem = model_output_file.relative_to(model_outputs)
        filename = model_output_file.name[:-5] # strip .yaml
        model_id = str(list(stem.parents)[0])
        task_prefix = filename.split("-")[0]

        try:
            output = yaml_decode(model_output_file.read_text(), ModelOutput)
        except yaml.error.YAMLError as err:
            raise ValueError(f"Unable to parse model output file: {model_output_file}: {str(err)}") from err

        label = "Bad"
        unexpected_states = output.context["unexpected_states"]
        if len(unexpected_states) == 0:
            # Success!
            label = "Good"
            if "Sorry" in output.response:
                raise ValueError(f"Incorrect expected states logic? Response said Sorry but no unexpeted states: {output.task_id}")
        print_row({
            "model_id": model_id,
            "category": output.category,
            "task_prefix": task_prefix,
            "label": label,
            "text": output.task["input_text"],
            "response": output.response,
            "tool_call": find_llm_call(output.context.get("conversation_trace", {})),
            "entity_diff": print_diff(unexpected_states)
        })

    return 0
