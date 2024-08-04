"""Build the llm leaderboard based on the pre-build eval results.

```
usage: home-assistant-datasets leaderboard build [-h] [--report-dir REPORT_DIR]

options:
  -h, --help            show this help message and exit
  --report-dir REPORT_DIR
                        Specifies the report dataset directory created by `eval` commands
```
"""

import argparse
import logging
from dataclasses import dataclass
from collections.abc import Callable
import math
import pathlib

import yaml

from .config import (
    REPORT_DIR,
    DATASETS,
    eval_reports,
    COLORS,
)


__all__ = []

_LOGGER = logging.getLogger(__name__)

LEADERBOARD_FILE = "leaderboard.md"


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--report-dir",
        type=str,
        default=REPORT_DIR,
        help="Specifies the report dataset directory created by `eval` commands",
    )


@dataclass
class ModelRecord:
    model_id: str
    dataset: str
    dataset_label: str
    good: int
    total: int
    good_percent: str

    def good_percent_value(self) -> float:
        return self.good / self.total

    @property
    def stddev(self) -> float:
        """Compute the stddev of the score."""
        p = self.good_percent_value()
        return math.sqrt((p * (1 - p)) / self.total)


def best_score_func(
    model_scores: dict[str, dict[str, ModelRecord]], dataset_name: str
) -> Callable[[str], float]:
    """Best score function."""

    def func(model_id: str) -> float:
        records = model_scores[model_id][dataset_name]
        return records[0].good_percent_value() if records else 0

    return func


def run(args: argparse.Namespace) -> int:
    """Run the command line action."""
    report_dir = pathlib.Path(args.report_dir)

    model_scores: dict[str, dict[str, list[ModelRecord]]] = {}
    for eval_report in eval_reports(report_dir):
        report_file = eval_report.report_file
        if not report_file.exists:
            raise ValueError(
                f"Report file {report_file} does not exist, run `prebuild` first"
            )

        report = yaml.load(eval_report.report_file.read_text(), Loader=yaml.CSafeLoader)
        for model_data in report:
            model_id = model_data["model_id"]
            if model_id not in model_scores:
                model_scores[model_id] = {}
            if eval_report.dataset not in model_scores[model_id]:
                model_scores[model_id][eval_report.dataset] = []

            model_scores[model_id][eval_report.dataset].append(
                ModelRecord(
                    **model_data,
                    dataset=eval_report.dataset,
                    dataset_label=eval_report.dataset_label,
                )
            )

    # Sort reports by their best scores
    for model_id in model_scores:
        for dataset in DATASETS:
            if dataset not in model_scores[model_id]:
                model_scores[model_id][dataset] = []
            records = model_scores[model_id][dataset]
            records = sorted(records, key=ModelRecord.good_percent_value, reverse=True)
            model_scores[model_id][dataset] = records

    # Generate overall report sorted by the first dataset score
    best_score = best_score_func(model_scores, DATASETS[0])
    sorted_model_ids = sorted(model_scores.keys(), key=best_score, reverse=True)

    results = [
        ["| Model | ", " | ".join(DATASETS), "|"],
        ["| ----- " * (len(DATASETS) + 1), "|"],
    ]
    for model_id in sorted_model_ids:
        row = [f"| {model_id} "]
        for dataset in DATASETS:
            records = model_scores[model_id][dataset]
            if records:
                best_record = records[0]
                row.append(
                    f"| {best_record.good_percent_value()*100:0.1f}% (+/- {best_record.stddev*100:0.1f}%) {best_record.dataset_label} "
                )
            else:
                row.append("| 0 ")
        row.append("|")
        results.append(row)

    # Generate a bar chart for each dataset
    for dataset in DATASETS:

        best_score = best_score_func(model_scores, dataset)
        sorted_model_ids = sorted(model_scores.keys())

        x_axis = []
        bar = []

        for model_id in sorted_model_ids:
            records = model_scores[model_id][dataset]
            x_axis.append(model_id)
            if not records:
                bar.append(0)
                continue
            best_record = records[0]
            #            x_axis.append(model_id)
            bar.append(float(f"{best_record.good_percent_value()*100:0.2f}"))

        def make_bar(index: int, bars: list[int]) -> str:
            values = ["0"] * len(bars)
            values[index] = str(bars[index])
            return ", ".join(values)

        x_axis_str = ", ".join([model_id for model_id in x_axis])
        color_str = ", ".join(COLORS[0 : len(sorted_model_ids)])
        bar_str = "\n".join(
            [
                f"  bar [{make_bar(index, bar)}]"
                for index, model_id in enumerate(sorted_model_ids)
            ]
        )
        results.extend(
            [
                "",
                f"""```mermaid
---
config:
    xyChart:
        width: 1500
        height: 800
        xAxis:
          labelFontSize: 12
          labelPadding: 8
    themeVariables:
        xyChart:
            titleColor: "#ff0000"
            plotColorPalette: "{color_str}"

---
xychart-beta
  title "{dataset}"
  x-axis "Model" [{x_axis_str}]
  y-axis "Score" 1 --> 100
{bar_str}
```
""",
            ]
        )

    leaderboard_file = report_dir / LEADERBOARD_FILE
    print(f"Updating {leaderboard_file}")
    leaderboard_file.write_text("\n".join(["".join(row) for row in results]))

    return 0
