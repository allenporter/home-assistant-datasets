"""Join the annotations with the original tasks and compute metrics by model."""

import argparse
import logging
import pathlib
import sys
import yaml

ANNOTATIONS = "annotations.yaml"

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

    annotations = model_outputs / ANNOTATIONS
    annotation_docs = yaml.load_all(annotations.read_text(), Loader=yaml.Loader)
    labels = {}
    for doc in annotation_docs:
        labels[doc["uuid"]] = doc["label"][0]

    model_results = {}

    output_files = model_outputs.glob("*/*.yaml")
    for output_file in output_files:
        model_id = output_file.parent.name
        if model_id not in model_results:
            model_results[model_id] = {}

        tasks = yaml.load_all(output_file.read_text(), Loader=yaml.Loader)
        for task in tasks:
            label = labels[task["uuid"]]
            model_results[model_id][label] = model_results[model_id].get(label, 0) + 1

    print(yaml.dump(model_results, sort_keys=True, explicit_start=True))


if __name__ == "__main__":
    main()
