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
import logging

import pytest


from home_assistant_datasets.tool.fixtures import configure_yaml

__all__ = []

_LOGGER = logging.getLogger(__name__)

PLUGINS = []


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
        "--dataset",
        type=str,
        help="Specifies the test dataset to load for evaluation",
    )
    args.add_argument(
        "test_path",
        help="A pytest pass through flag that is the directory containing the dataset to evaluate.",
        type=str,
        default="home_assistant_datasets/tool/assist/eval_tests/test_eval.py",
        nargs="?",
    )
    # Flags consistent with pytest for pass through
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
