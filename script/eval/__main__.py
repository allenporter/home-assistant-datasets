"""A command line tool that starts a Home Assistant instance and loads various states for performing evaluations."""

import argparse
import pathlib
import sys
import logging
import shutil


from . import driver

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
    arguments = parser.parse_args()
    return arguments


def main():
    """Evaluate an integration."""
    logging.basicConfig(level=logging.DEBUG)

    args = get_arguments()

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

    tool = driver.Driver(home_config_path.name, config_dir)
    tool.run_until_complete()
    if not tool.status:
        _LOGGER.error("Failed to create synthetic home")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
