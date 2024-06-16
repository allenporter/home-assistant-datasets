"""Home Assistant Datasets command line tools."""

import argparse
import importlib
import logging
import sys
from pathlib import Path

import asyncio

from . import assist_collect, assist_eval


_LOGGER = logging.getLogger(__name__)


def get_base_arg_parser() -> argparse.ArgumentParser:
    """Get a base argument parser."""
    parser = argparse.ArgumentParser(description="Home Assistant Datasets Utility")
    parser.add_argument("--debug", action="store_true", help="Enable log output")
    subparsers = parser.add_subparsers(dest="action", help="Action", required=True)

    # Subcommands
    assist_collect.create_arguments(subparsers.add_parser("assist_collect"))
    assist_eval.create_arguments(subparsers.add_parser("assist_eval"))

    return parser


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    return get_base_arg_parser().parse_known_args()[0]


def main() -> int:
    """Run a translation script."""
    if not Path("requirements_dev.txt").is_file():
        print("Run from project root")
        return 1

    args = get_arguments()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    module = importlib.import_module(f".{args.action}", "home_assistant_datasets.tool")
    _LOGGER.info("Running action %s", args.action)
    result: int = asyncio.run(module.run(args))
    return result


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print()
        print("Aborted!")
        sys.exit(2)
