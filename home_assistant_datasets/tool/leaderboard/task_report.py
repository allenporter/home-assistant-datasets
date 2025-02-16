"""Find information about tasks across all reports.

```
usage: home-assistant-datasets leaderboard task_report [-h] [--report-dir REPORT_DIR]

options:
  -h, --help            show this help message and exit
  --report-dir REPORT_DIR
                        Specifies the report dataset directory created by `eval` commands
```
"""

import argparse
from collections import Counter
import csv
import concurrent.futures
import logging
import pathlib
import subprocess
import yaml

from .config import REPORT_DIR, eval_reports

__all__ = []

_LOGGER = logging.getLogger(__name__)

TOP_N = 15

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

    total = Counter()
    bad = Counter()

    for eval_report in eval_reports(report_dir):
        with eval_report.csv_file.open() as fd:
            csvfile = csv.reader(fd)
            for row in csvfile:
                if not row or len(row) < 2:
                    continue
                task = row[1] # + "-" + row[4]
                total[task] +=1
                if row[3] == "Bad":
                    bad[task] += 1

    percent = Counter()
    for task in bad.elements():
        bad_count = bad.get(task)
        total_count = total.get(task)
        percent[task] = 100 * bad_count / total_count


    for task, percent in percent.most_common(TOP_N):
        bad_count = bad.get(task)
        print(f"{task} - {bad_count} - {100-percent:0.2f}%")

    return 0
