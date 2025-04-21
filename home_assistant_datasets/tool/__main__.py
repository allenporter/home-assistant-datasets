"""Home Assistant Datasets command line tools."""

import argparse
import importlib
import logging
import types
import sys
from pathlib import Path

# Ensure home assistant recorder is patched before actually loading
from pytest_homeassistant_custom_component import patch_recorder  # noqa: F401

from . import leaderboard, convert


_LOGGER = logging.getLogger(__name__)

SUBCMDS = {
    "leaderboard": leaderboard,
    "convert": convert,
}


def create_arguments(
    parser: argparse._SubParsersAction,
    subcmds: dict[str, types.ModuleType],
) -> None:
    """Recursively add sub commands/submodules and arguments to the parser"""
    for name, module in subcmds.items():
        cmd_parser = parser.add_parser(name)
        subparsers = cmd_parser.add_subparsers(
            dest="subaction", help="Sub Action", required=True
        )
        for inner_name, inner_module in module.SUBCMDS.items():
            inner_module.create_arguments(subparsers.add_parser(inner_name))


def get_base_arg_parser() -> argparse.ArgumentParser:
    """Get a base argument parser."""
    parser = argparse.ArgumentParser(description="Home Assistant Datasets Utility")
    parser.add_argument("--debug", action="store_true", help="Enable log output")
    subparsers = parser.add_subparsers(dest="action", help="Action", required=True)
    create_arguments(subparsers, SUBCMDS)

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

    if hasattr(args, "subaction"):
        module_name = f".{args.action}.{args.subaction}"
    else:
        module_name = f".{args.action}"

    module = importlib.import_module(module_name, "home_assistant_datasets.tool")
    _LOGGER.debug("Running action %s", module_name)
    result: int = module.run(args)
    return result


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print()
        print("Aborted!")
        sys.exit(2)
