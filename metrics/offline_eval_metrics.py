"""Analyze the results of labeling tasks and compute metrics for each model."""

import argparse
import logging
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

    model_results = {}
    for model_output_file in model_outputs.glob("*.yaml"):
        model_id = model_output_file.stem
        with model_output_file.open() as fd:
            annotation_docs = yaml.load_all(fd.read(), Loader=yaml.Loader)
        success = 0
        total = 0
        for record in annotation_docs:
            task = record["task"]["label"]
            response = record["response"]
            if task == response:
                success += 1
            total += 1
        ratio = (100.0 * success) / total
        model_results[model_id] = f"{ratio:0.1f}%"

    print(yaml.dump(model_results, sort_keys=True, explicit_start=True))


if __name__ == "__main__":
    main()
