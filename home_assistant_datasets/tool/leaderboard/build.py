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
import math
import pathlib

import yaml

from home_assistant_datasets import data_model

from .config import (
    REPORT_DIR,
    DATASETS,
    eval_reports,
)
from . import table, chart


__all__ = []

_LOGGER = logging.getLogger(__name__)

LEADERBOARD_FILE = "README.md"

IMPLEMENTATION_NOTES = """
Implementation notes:
- CI is large given small number of samples in the datasets.
- Note that not all models have been evaluated against all benchmarks. If a model is missing a run against a dataset, it just means it has not been evaluated.
- Error bars are std dev based on the # of tasks in the dataset.
- Local models evaluated using a GeForce GTX 1070 (8GB).
- Local models quantized with either Q4_K_M or Q4_0 but see links below for details.
- Temperature settings are based on the default values used in integrations.
"""

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
        if not self.total:
            return 0
        return self.good / self.total

    @property
    def stddev(self) -> float:
        """Compute the stddev of the score."""
        if not self.total:
            return 0
        p = self.good_percent_value()
        return math.sqrt((p * (1 - p)) / self.total)


def parse_model_reports(
    report_dir: pathlib.Path,
) -> dict[str, dict[str, list[ModelRecord]]]:
    """Read the model report files and parse into a map by model and dataset."""
    model_scores: dict[str, dict[str, list[ModelRecord]]] = {}
    for eval_report in eval_reports(report_dir):
        report_file = eval_report.report_file
        if not report_file.exists():
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
    return model_scores


def compute_best_scores(
    model_scores: dict[str, dict[str, list[ModelRecord]]]
) -> dict[str, dict[str, ModelRecord]]:
    """Compute the highest score for each model and dataset, filling in zero values where needed."""
    best_model_scores: dict[str, dict[str, ModelRecord]] = {}
    for model_id in model_scores:
        best_model_scores[model_id] = {}
        for dataset in DATASETS:
            if dataset not in model_scores[model_id]:
                best_model_scores[model_id][dataset] = ModelRecord(
                    model_id=model_id,
                    dataset=dataset,
                    dataset_label="",
                    good=0,
                    total=0,
                    good_percent="",
                )
            else:
                records = model_scores[model_id][dataset]
                records = sorted(
                    records, key=ModelRecord.good_percent_value, reverse=True
                )
                best_model_scores[model_id][dataset] = records[0]
    # Generate overall report sorted by the first dataset score
    sorted_model_ids = sorted(
        best_model_scores.keys(),
        key=lambda x: best_model_scores[x][DATASETS[0]].good_percent_value(),
        reverse=True,
    )
    return {model_id: best_model_scores[model_id] for model_id in sorted_model_ids}


def create_leaderboard_table(
    best_model_scores: dict[str, dict[str, ModelRecord]]
) -> str:
    """Create leaderboard markdown table."""
    cols = ["Model"]
    first_model_id = next(iter(best_model_scores.keys()))
    for dataset in DATASETS:
        assert best_model_scores[first_model_id][dataset]
        num_samples = best_model_scores[first_model_id][dataset].total
        cols.append(f"{dataset} (n={num_samples})")
    rows = []
    for model_id, dataset_scores in best_model_scores.items():
        row = [ model_id ]
        for dataset, best_record in dataset_scores.items():
            if best_record.good_percent_value() != 0:
                ci = 1.96 * best_record.stddev*100
                row.append(f"{best_record.good_percent_value()*100:0.1f}% (CI:&nbsp;{ci:0.1f}%, {best_record.dataset_label})")
            else:
                row.append("")
        rows.append(row)
    return table.table(cols, rows)


def run(args: argparse.Namespace) -> int:
    """Run the command line action."""
    report_dir = pathlib.Path(args.report_dir)

    model_scores = parse_model_reports(report_dir)
    best_model_scores = compute_best_scores(model_scores)

    # Models in the config file are ranked/grouped logically for display display.
    # These models may not be present in the reports, however.
    ranked_model_ids = {
        model.model_id: model
        for model in data_model.read_models().models
        if model.model_id in best_model_scores
    }
    dataset_cards = {
        dataset_card.name: dataset_card
        for dataset_card in data_model.read_dataset_cards()
        if dataset_card.name in DATASETS
    }

    # Markdown table with top model results
    leaderboard_table = create_leaderboard_table(best_model_scores)

    results = [
        "# Home LLM Leaderboard",
        leaderboard_table,
        IMPLEMENTATION_NOTES,
        "## Datasets",
    ]

    # TODO: Group models based on a rank of # of parameters (cloud, local, etc)
    # Use a fix set of colors for the model
    model_colors = chart.color_map(best_model_scores.keys())
    # Generate a bar chart for each dataset
    for dataset in DATASETS:
        models = []
        scores = []
        for model_id in ranked_model_ids:
            best_record = best_model_scores[model_id][dataset]
            if best_record.good_percent_value() == 0:
                continue
            models.append(model_id)
            scores.append(best_record.good_percent_value() * 100)

        # Add an empty value to give more space outside of the controls
        models.append(".")
        scores.append(-1)

        dataset_chart = chart.DatasetChart(
            dataset=dataset, models=models, scores=scores
        )
        chart_markdown = chart.model_xy_chart(dataset_chart, model_colors=model_colors)

        results.append(table.format_dataset_card(dataset_cards[dataset]))
        results.append(chart_markdown)

    results.append("## Models")
    for model_card in ranked_model_ids.values():
        results.append(table.format_model_card(model_card))

    leaderboard_file = report_dir / LEADERBOARD_FILE
    print(f"Updating {leaderboard_file}")
    leaderboard_file.write_text("\n".join(["".join(row) for row in results]))

    return 0
