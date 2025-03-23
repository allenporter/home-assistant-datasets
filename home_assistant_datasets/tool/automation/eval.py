"""Evaluate solutions to the automation problems.

This is configured similarly to an assist dataset collection tool, however
it uses tooling for creating automations. See the `collect` tool for usage
details.

Usage:
```
usage: home-assistant-datasets automation eval [-h] [--model_output_dir MODEL_OUTPUT_DIR] [--report_dir REPORT_DIR] [--collect-only] [-s]
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
```
"""

import argparse
import logging

import pytest

from home_assistant_datasets.tool.fixtures.conftest import configure_yaml

__all__ = []

_LOGGER = logging.getLogger(__name__)

DEFAULT_DATASET = "datasets/automations"
PLUGINS = [
    "home_assistant_datasets.fixtures",
]


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--model_output_dir",
        type=str,
        help="Specifies the model output directory from `collect`.",
    )
    args.add_argument(
        "--dataset",
        type=str,
        help="Specifies the test dataset to load for evaluation",
        default=DEFAULT_DATASET,
        required=True,
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
    # The dataset path contains tests
    pytest_args.append(args.dataset)

    configure_yaml()

    retcode = pytest.main(
        pytest_args,
        plugins=PLUGINS,
    )
    return retcode
