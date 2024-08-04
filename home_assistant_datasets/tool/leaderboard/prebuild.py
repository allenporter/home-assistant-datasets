"""Build all the assist eval reports needed to build the leaderboard.

```
usage: home-assistant-datasets leaderboard prebuild [-h] [--report-dir REPORT_DIR]

options:
  -h, --help            show this help message and exit
  --report-dir REPORT_DIR
                        Specifies the report dataset directory created by `eval` commands
```
"""

import argparse
import logging
import pathlib
import subprocess


from .config import REPORT_DIR, eval_reports

__all__ = []

_LOGGER = logging.getLogger(__name__)


EVAL_CMD = [
    "home-assistant-datasets",
    "assist",
    "eval",
    "--output_type=report",
]


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--report-dir",
        type=str,
        default=REPORT_DIR,
        help="Specifies the report dataset directory created by `eval` commands",
    )


def run(args: argparse.Namespace) -> int:
    """Run the command line action."""
    report_dir = pathlib.Path(args.report_dir)

    for eval_report in eval_reports(report_dir):
        print(f"Generating report for outputs in {eval_report.directory}")
        cmds = EVAL_CMD + [f"--model_output_dir={eval_report.directory}"]
        _LOGGER.debug(cmds)
        p = subprocess.Popen(cmds, stdout=subprocess.PIPE)
        (report_output, _) = p.communicate()
        if p.returncode:
            return p.returncode

        output_file = eval_report.report_file
        output_file.write_bytes(report_output)
        print(f"Writing {output_file}")

    return 0
