"""A command line tool that starts a Home Assistant instance and loads various states for performing evaluations."""

import argparse
import pathlib
import sys
import logging
import shutil

from . import config_driver, eval_driver


_LOGGER = logging.getLogger(__name__)

CONFIG_DIR = "config"


def get_arguments() -> argparse.Namespace:
    """Get parsed passed in arguments."""
    parser = argparse.ArgumentParser(description="Synthetic Home Evaluation Driver")
    parser.add_argument(
        "--config",
        type=str,
        help="The yaml configuration file with synthetic home data.",
        required=True,
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        help="The output directory which is overwritten with the results.",
        required=True,
    )
    subparsers = parser.add_subparsers(dest="func")
    subparsers.required = True

    parser_create_config = subparsers.add_parser("create_config")
    parser_create_config.set_defaults(func=create_config)

    parser_eavl = subparsers.add_parser("eval")
    parser_eavl.set_defaults(func=eval)

    return parser.parse_args()


def create_config(args: argparse.Namespace) -> None:
    """Run the create config command."""
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    config_dir = output_dir / CONFIG_DIR
    shutil.rmtree(config_dir, ignore_errors=True)
    config_dir.mkdir()

    home_config_path = pathlib.Path(args.config)
    with home_config_path.open() as fd:
        content = fd.read()
        with (config_dir / home_config_path.name).open("w") as out:
            out.write(content)

    config_driver.ConfigDriver(home_config_path.name, config_dir).run_until_complete()


def eval(args: argparse.Namespace) -> None:
    """Run the evaluation command."""
    output_dir = pathlib.Path(args.output_dir)
    config_dir = output_dir / CONFIG_DIR
    home_config_path = pathlib.Path(args.config)
    eval_driver.EvalDriver(home_config_path.name, config_dir).run_until_complete()


def main():
    """Evaluate an integration."""
    logging.basicConfig(level=logging.DEBUG)

    args = get_arguments()
    args.func(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
