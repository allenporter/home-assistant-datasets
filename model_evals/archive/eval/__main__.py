"""A command line tool that starts a Home Assistant instance and loads various states for performing evaluations."""

import argparse
import pathlib
import sys
import logging
import tempfile

from . import eval_driver, runner
from . import loader  # noqa: F401


_LOGGER = logging.getLogger(__name__)

TMPDIR_PREFIX = "homeassistant-eval"
CONFIG_DIR = "config"
EVAL_CONFIG_FILE = "config.yaml"


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
        "--eval_dir",
        type=str,
        help="The evaluation configuration directory.",
        required=True,
    )
    parser.add_argument(
        "--delete_tmpdir",
        default=True,
        help="If disabled, will keep the Home Assistant directory for inspection.",
        action=argparse.BooleanOptionalAction
    )
    return parser.parse_args()


def run_eval(args: argparse.Namespace) -> bool:
    """Prepare and run the evaluation command"""

    eval_dir = pathlib.Path(args.eval_dir)

    with tempfile.TemporaryDirectory(prefix=TMPDIR_PREFIX, delete=args.delete_tmpdir) as tmp_dir:
        config_dir = pathlib.Path(tmp_dir) / CONFIG_DIR
        config_dir.mkdir()

        driver = eval_driver.EvalDriver(eval_dir)

        runtime_config = runner.RuntimeConfig(
            config_dir=str(config_dir),
            load_registries=False,
            load_config_entries=True,
            setup_callback=driver.async_setup,
            run_callback=driver.async_run,
        )
        return runner.run(runtime_config)


def main() -> int:
    """Evaluate an integration."""
    args = get_arguments()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))
    result = run_eval(args)
    if result != 0:
        print(f"Failed with exit code {result}", file=sys.stderr)
    return result


if __name__ == "__main__":
    sys.exit(main())
