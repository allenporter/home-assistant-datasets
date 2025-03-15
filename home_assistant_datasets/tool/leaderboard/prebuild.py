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
import concurrent.futures
import logging
import pathlib
import subprocess

from .config import REPORT_DIR, eval_reports, EvalReport, ASSIST_FAMILY_DATASETS

__all__ = []

_LOGGER = logging.getLogger(__name__)


EVAL_CMD = [
    "home-assistant-datasets",
    "assist",
    "eval",
]
WORKERS = 5


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

    def write_eval_output(cmds: list[str], output_file: pathlib.Path) -> None:
        _LOGGER.debug(cmds)
        p = subprocess.Popen(cmds, stdout=subprocess.PIPE)
        (report_output, _) = p.communicate()
        if p.returncode:
            raise ValueError("Error writing eval output")
        print(f"Writing {output_file}")
        output_file.write_bytes(report_output)

    def build_report(eval_report: EvalReport) -> None:
        print(f"Generating report for outputs in {eval_report.directory}")
        cmds = EVAL_CMD + [
            "--output_type=report",
            f"--model_output_dir={eval_report.directory}",
        ]
        write_eval_output(cmds, eval_report.report_file)
        cmds = EVAL_CMD + [
            "--output_type=csv",
            f"--model_output_dir={eval_report.directory}",
        ]
        write_eval_output(cmds, eval_report.csv_file)

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(build_report, eval_report)
            for eval_report in eval_reports(report_dir, datasets=ASSIST_FAMILY_DATASETS)
        }
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print("Task generated an exception: %s" % exc)

    return 0
