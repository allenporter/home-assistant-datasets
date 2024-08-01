"""Evaluate data collected from the home assistant conversation agent.

See `assist_collect` for the step to collect data. You can then run an offline
analysis of the model using the following command:

```bash
$ OUTPUT_DIR="output/$(date +"%Y-%m-%d")/"
$ home-assistant-datasets assist eval --model_output_dir=${OUTPUT_DIR}
```

"""

import argparse
import logging
import pathlib
from typing import Any

import yaml
from mashumaro.mixins.yaml import EncodedData

from homeassistant.components.conversation import trace

from .data_model import ModelOutput


_LOGGER = logging.getLogger(__name__)

GOOD_LABEL = "Good"
BAD_LABEL = "Bad"

def find_llm_call(trace_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Gets the llm call from the conversation trace."""
    tool_call = next(
        iter(
            event
            for event in trace_events
            if event["event_type"] in (trace.ConversationTraceEventType.TOOL_CALL, "llm_tool_call")
        ),
        None,
    )
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
        val = val.replace('"', "'")
        vals.append(f'"{val}"')
    print(",".join(vals))

model_totals: dict[str, int] = {}
model_good: dict[str, int] = {}


def handle_report_row(row: dict[str, Any]) -> None:
    """Handle a report row collecting the # of good labels for each model."""
    model_id = row["model_id"]
    if model_id not in model_totals:
        model_totals[model_id] = 0
        model_good[model_id] = 0
    model_totals[model_id] += 1
    if row["label"] == GOOD_LABEL:
        model_good[model_id] += 1

def handle_report_summary() -> None:
    """Print the report summary"""
    items = [
        {
            "model_id": model_id,
            "good_percent": f"{100*(model_good[model_id] / total):0.1f}%",
            "good": model_good[model_id],
            "total": total,
        }
        for model_id, total in model_totals.items()
    ]
    print(yaml.dump(items, sort_keys=False, explicit_start=True))


def yaml_decoder(data: EncodedData) -> dict[Any, Any]:
    return yaml.load(data, yaml.UnsafeLoader)


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
    """Run the command line action."""
    model_outputs = pathlib.Path(args.model_output_dir)
    if args.output_type == "csv":
        print(",".join(COLUMNS))
    print_diff = dict
    print_summary = lambda: None
    if args.output_type == "csv":
        print_row = print_csv_row
        print_diff = str
    elif args.output_type == "yaml":
        print_row = print_yaml_row
    elif args.output_type == "report":
        print_row = handle_report_row
        print_summary = handle_report_summary
    else:
        raise ValueError("Invalid value for --output_type")

    model_totals: dict[str, int] = {}
    model_good: dict[str, int] = {}


    for model_output_file in model_outputs.glob("**/*.yaml"):
        stem = model_output_file.relative_to(model_outputs)
        filename = model_output_file.name[:-5]  # strip .yaml
        model_id = str(list(stem.parents)[0])
        task_prefix = filename.split("-")[0]

        try:
            output = ModelOutput.from_yaml(
                model_output_file.read_text(), decoder=yaml_decoder
            )
        except (yaml.error.YAMLError, ValueError) as err:
            raise ValueError(
                f"Unable to parse model output file: {model_output_file}: {str(err)}"
            ) from err

        label = BAD_LABEL
        unexpected_states = output.context["unexpected_states"]
        if len(unexpected_states) == 0:
            # Success!
            label = GOOD_LABEL
            if "Sorry" in output.response:
                raise ValueError(
                    f"Incorrect expected states logic in {model_output_file}? Response said Sorry but no unexpected states: {output.task_id}"
                )
        print_row(
            {
                "model_id": model_id,
                "category": output.category,
                "task_prefix": task_prefix,
                "label": label,
                "text": output.task["input_text"],
                "response": output.response,
                "tool_call": find_llm_call(
                    output.context.get("conversation_trace", {})
                ),
                "entity_diff": print_diff(unexpected_states),
            }
        )

    print_summary()

    return 0
