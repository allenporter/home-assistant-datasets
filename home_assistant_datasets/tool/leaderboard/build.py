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

from home_assistant_datasets.datasets.dataset_card import read_dataset_cards
from home_assistant_datasets.models import read_models

from .config import (
    REPORT_DIR,
    DATASETS,
    SCORED_DATASETS,
    AVERAGE_SCORE,
    DATASETS_FOR_AVG,
    ASSIST_DATASET,
    LANGUAGES,
    LANGUAGE_NAMES,
    MULTILINGUAL_DATASETS,
    ALL_MULTILINGUAL_DATASET_NAMES,
    eval_reports,
)
from .eval_cost import compute_model_eval_cost
from . import table, chart


__all__ = []

_LOGGER = logging.getLogger(__name__)

LEADERBOARD_FILE = "README.md"

IMPLEMENTATION_NOTES = """
Implementation notes:
- CI is large given small number of samples in the datasets.
- Note that not all models have been evaluated against all benchmarks. If a model is missing a run against a dataset, it just means it has not been evaluated.
- Error bars are std dev based on the # of tasks in the dataset.
- Local models quantized with either Q4_K_M or Q4_0 but see links below for details.
- Most small local models evaluated using a GeForce GTX 1070 (8GB). Larger models were contributed by other hardware mixes.
- Temperature settings are based on the default values used in integrations.
"""

TOP_N = 12


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
    good_percent: str | None = None

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

    @property
    def confidence_interval(self) -> float:
        """Compute the confidence interval of the score."""
        if not self.total:
            return 0
        return 1.96 * self.stddev * 100


def parse_model_reports(
    report_dir: pathlib.Path,
) -> dict[str, dict[str, list[ModelRecord]]]:
    """Read the model report files and parse into a map by model and dataset."""
    model_scores: dict[str, dict[str, list[ModelRecord]]] = {}
    for eval_report in eval_reports(report_dir, DATASETS):
        report_file = eval_report.report_file
        if not report_file.exists():
            raise ValueError(
                f"Report file {report_file} does not exist, make sure `eval` is run first"
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
                    model_id=model_id,
                    dataset=eval_report.dataset,
                    dataset_label=eval_report.dataset_label,
                    good=model_data["good"],
                    total=model_data["total"],
                    good_percent=model_data.get("good_percent"),
                )
            )
    return model_scores


def compute_best_scores(
    model_scores: dict[str, dict[str, list[ModelRecord]]],
) -> dict[str, dict[str, ModelRecord]]:
    """Compute the highest score for each model and dataset, filling in zero values where needed."""
    best_model_scores: dict[str, dict[str, ModelRecord]] = {}
    for model_id in model_scores:
        dataset_records = {}
        for dataset in DATASETS:
            if dataset not in model_scores[model_id]:
                dataset_records[dataset] = ModelRecord(
                    model_id=model_id,
                    dataset=dataset,
                    dataset_label="",
                    good=0,
                    total=0,
                )
            else:
                records = model_scores[model_id][dataset]
                records = sorted(
                    records, key=ModelRecord.good_percent_value, reverse=True
                )
                dataset_records[dataset] = records[0]

        # Compute the average as a synthetic record
        tot = sum(
            record.total
            for record in dataset_records.values()
            if record.total > 0 and record.dataset in DATASETS_FOR_AVG
        )
        good = sum(
            record.good
            for record in dataset_records.values()
            if record.total > 0 and record.dataset in DATASETS_FOR_AVG
        )
        avg_record = ModelRecord(
            model_id,
            dataset=AVERAGE_SCORE,
            dataset_label=AVERAGE_SCORE,
            good=good,
            total=tot,
        )
        dataset_records[AVERAGE_SCORE] = avg_record
        best_model_scores[model_id] = dataset_records

    def score_sort_key(model_id: str) -> list[float]:
        """Sort by dataset scores in order."""
        records = [
            best_model_scores[model_id].get(dataset) for dataset in SCORED_DATASETS
        ]
        return [record.good_percent_value() if record else 0 for record in records]

    # Generate overall report sorted by the first dataset score
    sorted_model_ids = sorted(
        best_model_scores.keys(),
        key=score_sort_key,
        reverse=True,
    )
    return {model_id: best_model_scores[model_id] for model_id in sorted_model_ids}


def compute_best_dataset_scores(
    best_model_scores: dict[str, dict[str, ModelRecord]],
) -> dict[str, set[str]]:
    """Compute the models that scored highest on each dataset."""
    best_dataset_scores = {}
    for dataset in SCORED_DATASETS:
        max = 0.0
        best: set[str] = set({})
        for model in best_model_scores:
            if (record := best_model_scores[model].get(dataset)) is None:
                continue
            value = record.good_percent_value()
            if value > max:
                max = value
                best = {model}
            elif value >= max:
                best = best | {model}
        best_dataset_scores[dataset] = best
    return best_dataset_scores


def create_leaderboard_table(
    best_model_scores: dict[str, dict[str, ModelRecord]],
) -> str:
    """Create leaderboard markdown table."""
    cols = ["Model"]
    first_model_id = next(iter(best_model_scores.keys()))
    for dataset in DATASETS:
        assert best_model_scores[first_model_id][dataset]
        num_samples = best_model_scores[first_model_id][dataset].total
        text = [
            dataset,
            " ",
            "$${\\color{gray}",
            "\\small{\\textsf{",
            f"(n={num_samples})",
            "}}",  # end small text
            "}$$",
        ]
        cols.append("".join(text))

    best_dataset_scores = compute_best_dataset_scores(best_model_scores)

    rows = []
    for model_id, dataset_scores in best_model_scores.items():
        row = [model_id]
        for dataset, best_record in dataset_scores.items():
            if best_record.total == 0:
                row.append("")
                continue
            ci = best_record.confidence_interval
            text_parts = [
                "$${",
            ]
            best_tag = ""
            if model_id in best_dataset_scores[dataset]:
                best_tag = " * \\space"
            score = best_record.good_percent_value()
            score_str = f"{score * 100:0.1f}"
            if model_id in best_dataset_scores[dataset]:
                score_str = "\\textbf{" + score_str + "}"
            text_parts.extend(
                [
                    score_str,
                    "\\\\% \\space",  # % sign
                    best_tag,
                    # Put the CI and dataset label in small gray text
                    "\\color{gray}\\tiny{\\textsf{",
                    f"(CI: {ci:0.1f}, {best_record.dataset_label})",
                    "}}",  # end small text
                    "}$$",
                ]
            )
            row.append("".join(text_parts))
        rows.append(row)
    return table.table(cols, rows)


def compute_multilingual_best_scores(
    report_dir: pathlib.Path,
    active_model_ids: set[str],
) -> dict[str, dict[str, ModelRecord]]:
    """Parse multilingual reports and compute best score per dataset per model.

    Returns a dict keyed by dataset name (e.g. "assist-es") mapping to
    a dict of model_id -> best ModelRecord for that dataset.
    """
    scores: dict[str, dict[str, ModelRecord]] = {}
    for eval_report in eval_reports(report_dir, ALL_MULTILINGUAL_DATASET_NAMES):
        report_file = eval_report.report_file
        if not report_file.exists():
            continue

        report = yaml.load(report_file.read_text(), Loader=yaml.CSafeLoader)
        for model_data in report:
            model_id = model_data["model_id"]
            if model_id not in active_model_ids:
                continue
            dataset = eval_report.dataset
            record = ModelRecord(
                model_id=model_id,
                dataset=dataset,
                dataset_label=eval_report.dataset_label,
                good=model_data["good"],
                total=model_data["total"],
                good_percent=model_data.get("good_percent"),
            )
            if dataset not in scores:
                scores[dataset] = {}
            existing = scores[dataset].get(model_id)
            if (
                existing is None
                or record.good_percent_value() > existing.good_percent_value()
            ):
                scores[dataset][model_id] = record

    return scores


def _format_score_cell(record: ModelRecord) -> str:
    """Format a score cell for the multilingual table."""
    score = record.good_percent_value()
    ci = record.confidence_interval
    return f"{score * 100:0.1f}% (CI: {ci:0.1f})"


def create_multilingual_section(
    best_model_scores: dict[str, dict[str, ModelRecord]],
    multilingual_scores: dict[str, dict[str, ModelRecord]],
) -> str:
    """Create the multilingual leaderboard section.

    Generates a per-base-dataset table with models as rows and languages as columns.
    """
    # Determine which models to show: top models from main leaderboard
    # that have at least one multilingual score
    models_with_multilingual = set()
    for dataset_scores in multilingual_scores.values():
        models_with_multilingual.update(dataset_scores.keys())

    # Use main leaderboard order, take models that have multilingual results
    display_models = [
        model_id
        for model_id in best_model_scores
        if model_id in models_with_multilingual
    ]

    if not display_models:
        return ""

    sections = ["## Multilingual"]

    for base_dataset in MULTILINGUAL_DATASETS:
        lang_datasets = MULTILINGUAL_DATASETS[base_dataset]
        # Check if any multilingual scores exist for this base dataset
        has_scores = any(
            ds in multilingual_scores and multilingual_scores[ds]
            for ds in lang_datasets
        )
        if not has_scores:
            continue

        sections.append(f"\n### {base_dataset} (multilingual)\n")

        # Columns: Model, then English, then each language
        all_langs = ["en"] + LANGUAGES
        cols = ["Model"] + [f"{lang} ({LANGUAGE_NAMES[lang]})" for lang in all_langs]
        rows = []

        for model_id in display_models:
            row = [model_id]
            # English score from main leaderboard
            record = best_model_scores.get(model_id, {}).get(base_dataset)
            if record and record.total > 0:
                row.append(_format_score_cell(record))
            else:
                row.append("\u2014")
            # Multilingual scores
            for lang in LANGUAGES:
                lang_dataset = f"{base_dataset}-{lang}"
                record = multilingual_scores.get(lang_dataset, {}).get(model_id)
                if record and record.total > 0:
                    row.append(_format_score_cell(record))
                else:
                    row.append("\u2014")
            rows.append(row)

        sections.append(table.table(cols, rows))

    if len(sections) <= 1:
        return ""

    return "\n".join(sections)


def run(args: argparse.Namespace) -> int:
    """Run the command line action."""
    report_dir = pathlib.Path(args.report_dir)

    active_models = {model.model_id: model for model in read_models().models}
    model_scores = parse_model_reports(report_dir)
    model_scores = {
        model_id: v for model_id, v in model_scores.items() if model_id in active_models
    }

    best_model_scores = compute_best_scores(model_scores)

    # Models in the config file are ranked/grouped logically for display display.
    # These models may not be present in the reports, however.
    ranked_model_ids = {
        model.model_id: model
        for model in active_models.values()
        if model.model_id in best_model_scores
    }
    dataset_cards = {
        dataset_card.name: dataset_card
        for dataset_card in read_dataset_cards()
        if dataset_card.name in DATASETS
    }
    eval_cost = compute_model_eval_cost(report_dir / ASSIST_DATASET)

    # Markdown table with top model results
    leaderboard_table = create_leaderboard_table(best_model_scores)

    # Multilingual section (only shown if multilingual reports exist)
    multilingual_scores = compute_multilingual_best_scores(
        report_dir, set(active_models.keys())
    )
    multilingual_section = create_multilingual_section(
        best_model_scores, multilingual_scores
    )

    results = [
        "# Home LLM Leaderboard",
        leaderboard_table,
        IMPLEMENTATION_NOTES,
    ]

    if multilingual_section:
        results.append(multilingual_section)

    results.append("## Datasets")

    # Use a fix set of colors for the model
    model_colors = chart.color_map(best_model_scores.keys())
    # Generate a bar chart for each dataset
    for dataset in DATASETS:
        models = []
        scores = []
        for model_id, records in best_model_scores.items():
            best_record = records[dataset]
            if best_record.good_percent_value() == 0:
                continue
            models.append(model_id)
            scores.append(best_record.good_percent_value() * 100)
            if len(models) >= TOP_N:
                break

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
        results.append(
            table.format_model_card(model_card, eval_cost.get(model_card.model_id))
        )

    leaderboard_file = report_dir / LEADERBOARD_FILE
    print(f"Updating {leaderboard_file}")
    leaderboard_file.write_text("\n".join(["".join(row) for row in results]))

    return 0
