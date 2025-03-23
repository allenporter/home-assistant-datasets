"""Evaluate data collected from the home assistant conversation agent.

See `assist_collect` for the step to collect data. You can then run an offline
analysis of the model using the following command:

```bash
usage: home-assistant-datasets assist eval [-h] [--model_output_dir MODEL_OUTPUT_DIR] [--report_dir REPORT_DIR] [--collect-only] [-s]
                                           [--verbose | --verbosity N]
                                           [test_path]

positional arguments:
  test_path             A pytest pass through flag that is the directory containing the dataset to evaluate.

options:
  -h, --help            show this help message and exit
  --model_output_dir MODEL_OUTPUT_DIR
                        Specifies the model output directory from `collect`.
  --report_dir REPORT_DIR
                        Specifies the directory where the report will be written, or defaults to --model_output_dir.
  --collect-only        A pytest pass through flag to only collect the list of tests without actually running them.
  -s                    A pytest pass through flag to show streaming test output.
  --verbose, -v         A pytest pass through flag to increase verbosity.
  --verbosity N         A pytest pass through flag to set verbosity. Default is 0
"""

import argparse
from dataclasses import dataclass
import logging
from typing import Any

import pytest

import yaml
from mashumaro.mixins.yaml import EncodedData

from homeassistant.components.conversation import trace

from home_assistant_datasets.tool.conftest import configure_yaml
from home_assistant_datasets.tool.data_model import (
    EvalMetric,
)

__all__ = []

_LOGGER = logging.getLogger(__name__)

PLUGINS = [
    #    "home_assistant_datasets.fixtures",
]


SKIP_COLUMNS = ["uuid"]


@dataclass(kw_only=True)
class AssistEvalMetric(EvalMetric):
    """Eval Metric for the assist dataset."""

    category: str
    task_prefix: str
    label: str
    text: str
    response: str
    tool_call: dict[str, Any] | None
    entity_diff: dict[str, Any] | str | None


def find_llm_call(trace_events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Gets the llm call from the conversation trace."""
    tool_call = next(
        iter(
            event
            for event in trace_events
            if event["event_type"]
            # type: ignore[attr-defined]
            in (trace.ConversationTraceEventType.TOOL_CALL, "llm_tool_call")
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


def yaml_decoder(data: EncodedData) -> Any:
    return yaml.load(data, yaml.UnsafeLoader)


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--model_output_dir",
        type=str,
        help="Specifies the model output directory from `collect`.",
    )
    args.add_argument(
        "--report_dir",
        type=str,
        help="Specifies the directory where the report will be written, or defaults to --model_output_dir.",
    )
    args.add_argument(
        "--collect-only",
        action="store_true",
        help="A pytest pass through flag to only collect the list of tests without actually running them.",
    )
    args.add_argument(
        "-s",
        action="store_true",
        help="A pytest pass through flag to show streaming test output.",
    )

    # Flags consistent with pytest for pass through
    args.add_argument(
        "test_path",
        help="A pytest pass through flag that is the directory containing the dataset to evaluate.",
        type=str,
        default="home_assistant_datasets/tool/automation/test_collect.py",
        nargs="?",
    )
    verbosity_group = args.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--verbose",
        "-v",
        action="count",
        dest="verbosity",
        help="A pytest pass through flag to increase verbosity.",
    )
    verbosity_group.add_argument(
        "--verbosity",
        action="store",
        type=int,
        metavar="N",
        dest="verbosity",
        help="A pytest pass through flag to set verbosity. Default is 0",
    )
    args.set_defaults(verbosity=0)


def run(args: argparse.Namespace) -> int:
    verbosity = args.verbosity
    pytest_args = [
        "--no-header",
        "--disable-warnings",
    ]
    if verbosity:
        pytest_args.extend(
            [
                "--verbosity",
                str(verbosity),
            ]
        )
    if args.test_path:
        pytest_args.append(args.test_path)
    if args.model_output_dir:
        pytest_args.extend(
            [
                "--model_output_dir",
                args.model_output_dir,
            ]
        )
    if args.report_dir:
        pytest_args.extend(
            [
                "--report_dir",
                args.report_dir,
            ]
        )

    if args.collect_only:
        pytest_args.append("--collect-only")
    if args.s:
        pytest_args.append("-s")
    configure_yaml()

    retcode = pytest.main(
        pytest_args,
        plugins=PLUGINS,
    )
    return retcode
