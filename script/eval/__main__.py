"""A command line tool that starts a Home Assistant instance and loads various states for performing evaluations."""

import argparse
import pathlib
import sys
import logging
import shutil

from . import config_driver, eval_driver, runner


_LOGGER = logging.getLogger(__name__)

CONFIG_DIR = "config"


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

    parser_eval = subparsers.add_parser("eval")
    parser_eval.set_defaults(func=eval)
    parser_eval.add_argument(
        "--agent_id",
        type=str,
        help="The conversation agent config entry id.",
        required=True,
    )

    return parser.parse_args()


def create_config(args: argparse.Namespace) -> int:
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

    driver = config_driver.ConfigDriver(home_config_path.name)
    runtime_config = runner.RuntimeConfig(
        config_dir=str(config_dir),
        load_registries=True,
        setup_callback=driver.async_setup,
        run_callback=driver.async_run,
    )
    return runner.run(runtime_config)


def eval(args: argparse.Namespace) -> None:
    """Run the evaluation command."""
    output_dir = pathlib.Path(args.output_dir)
    config_dir = output_dir / CONFIG_DIR
    home_config_path = pathlib.Path(args.config)

    driver = eval_driver.EvalDriver(home_config_path.name, args.agent_id)

    runtime_config = runner.RuntimeConfig(
        config_dir=str(config_dir),
        load_registries=False,
        run_callback=driver.async_run,
    )
    return runner.run(runtime_config)


def main():
    """Evaluate an integration."""
    args = get_arguments()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
