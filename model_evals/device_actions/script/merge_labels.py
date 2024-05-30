"""Join the annotations with the original tasks and compute metrics by model."""

import argparse
import logging
import pathlib
import sys
import yaml
import random

from typing import Any

_LOGGER = logging.getLogger(__name__)


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
        "--annotations_file",
        type=str,
        help="The name of the annotations file.",
        required=False,
    )
    parser.add_argument(
        "--output_format",
        type=str,
        default="yaml",
        help="The type of output files either yaml or csv.",
        required=False,
    )
    return parser.parse_args()


def load_uuid_labels(annotations: pathlib.Path) -> dict[str, str]:
    """Load labels for all tasks by uuid."""
    annotation_docs = yaml.load_all(annotations.read_text(), Loader=yaml.Loader)
    labels = {}
    for doc in annotation_docs:
        try:
            label = doc["label"][0]
        except IndexError as err:
            _LOGGER.info(f"Error extracting label from doc: {doc}: {err}")
            raise err
        labels[doc["uuid"]] = label
    return labels


def find_llm_call(trace: dict[str, Any]) -> str | None:
    """Gets the llm call."""
    events = trace.get("events", [])
    for event in events:
        if event["event_type"] == "llm_tool_call":
            data = event["data"]
            tool_name = data.get("tool_name")
            tool_args = data.get("tool_args", {})
            tool_args_str = ""
            if isinstance(tool_args, dict):
                tool_args_str = ",".join(
                    f"{k}={v}"
                    for k, v in tool_args.items()
                )
            return f"{tool_name}({tool_args_str})"
    return None

COLUMNS = [
    "model_id",
    "label",
    "device_type",
    "text",
    "response",
    "tool_call",
]

def convert_task_to_row(task: dict[str, Any]) -> dict[str, Any]:
    """Pull out the useful fields of the task for printing the row."""
    device_state = next(iter(task["task"]["device_states"]), {})
    #device_type = device_state.get("device_type", "none")
    tool_call = find_llm_call(task["context"].get("conversation_trace", {}))
    return {
        "text": task["task"]["input_text"],
        "response": task["response"],
        "tool_call": tool_call,
    }

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
    annotations = pathlib.Path(args.annotations_file)
    labels = load_uuid_labels(annotations)

    model_results = {}

    if args.output_format == "csv":
        print(",".join(COLUMNS))
    print_row = print_csv_row if args.output_format == "csv" else print_yaml_row

    output_files = model_outputs.glob("**/*.yaml")
    for output_file in output_files:
        stem = output_file.relative_to(model_outputs)
        model_id = str(list(stem.parents)[0])
        filename = output_file.name[:-5] # strip .yaml
        tasks = yaml.load_all(output_file.read_text(), Loader=yaml.Loader)
        for task in tasks:
            uid = task["uuid"]
            home_id = task["task"]["home_id"]
            device_type = filename[len(home_id)+1:]
            row = {
                "model_id": model_id,
                "label": labels.get(uid, "Unavailable"),
                "device_type": device_type,
                **convert_task_to_row(task)
            }
            print_row(row)



if __name__ == "__main__":
    main()
