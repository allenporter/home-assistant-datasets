"""Analyze the results of labeling tasks and compute metrics for each model."""

import argparse
from itertools import islice
import logging
from operator import itemgetter
import pathlib
import sys
import yaml

_LOGGER = logging.getLogger(__name__)


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
        "--model_outputs",
        type=str,
        help="The directory containing model outputs.",
        required=True,
    )
    return parser.parse_args()


def main():
    args = get_arguments()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    model_outputs = pathlib.Path(args.model_outputs)

    model_docs: dict[str, list[dict[str, str]]] = {}
    for model_output_file in model_outputs.glob("*.yaml"):
        model_id = model_output_file.stem
        with model_output_file.open() as fd:
            annotation_docs = list(yaml.load_all(fd.read(), Loader=yaml.Loader))
        model_docs[model_id] = annotation_docs

    # Compute leaderboard
    model_results = {}
    task_totals = {}
    task_success = {}
    task_text = {}
    for model_id, annotation_docs in model_docs.items():
        success = 0
        total = 0
        for record in annotation_docs:
            task_id = record["task_id"]
            if task_id not in task_text:
                task_text[task_id] = record["task"]["text"]
            task = record["task"]["label"]
            response = record["response"]
            if task == response:
                success += 1
                task_success[task_id] = task_success.get(task_id, 0) + 1
            total += 1
            task_totals[task_id] = task_totals.get(task_id, 0) + 1
        ratio = (100.0 * success) / total
        model_results[model_id] = f"{ratio:0.1f}%"

    leaderboard = dict(sorted(model_results.items(), key=itemgetter(1), reverse=True))

    task_scores = {
        task_id: 100 * task_success.get(task_id, 0) / total
        for task_id, total in task_totals.items()
    }
    hardest_tasks = dict(sorted(task_scores.items(), key=itemgetter(1), reverse=False))
    hardest_task_text = [
        f"{task_text[task_id]} ({score})"
        for task_id, score in islice(hardest_tasks.items(), 5)
    ]

    results = {
        "leaderboard": leaderboard,
        "hardest_tasks": hardest_task_text,
    }
    print(yaml.dump(results, sort_keys=False, explicit_start=True))

    # Most problematic


if __name__ == "__main__":
    main()
