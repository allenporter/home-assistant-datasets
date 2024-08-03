"""Build the llm leaderboard based on eval results.

"""

import argparse
import logging
import pathlib
import subprocess
from typing import Any

import yaml


__all__ = []

_LOGGER = logging.getLogger(__name__)

REPORT_DIR = "reports"
DATASETS = [
    "assist",
    "assist-mini",
    "intents",
]
IGNORE_REPORTS = {
    "reports/assist/2024.6.0dev-baseline-2024-05-27",
    "reports/assist/2024.6.0dev-v1-2024-05-27",
    "reports/assist/2024.6.0dev-v2-2024-05-29",
    "reports/assist/2024.6.0dev-v3-2024-05-31",
}
REPORT_FILE = "reports.yaml"


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

    for dataset in DATASETS:
        dataset_dir = report_dir / dataset
        for filename in dataset_dir.iterdir():
            if not filename.is_dir():
                continue
            if str(filename) in IGNORE_REPORTS:
                _LOGGER.debug("Ignoring report directory %s", filename)
                continue

            print(f"Generating report for outputs in {filename}")

            filename_parts = str(filename).split("/")
            assert filename_parts[0] == REPORT_DIR
            assert len(filename_parts) >= 3, filename_parts
            assert dataset == filename_parts[1], filename_parts
            dataset_label = filename_parts[2]
            print(f"Generating report for {dataset} {dataset_label}")

            cmds = EVAL_CMD + [f"--model_output_dir={filename}"]
            p = subprocess.Popen(cmds, stdout=subprocess.PIPE)
            (report_output, _) = p.communicate()
            if p.returncode:
                return p.returncode

            output_file = filename / REPORT_FILE
            output_file.write_bytes(report_output)
            print(f"Writing {output_file}")

    return 0
