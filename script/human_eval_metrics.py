"""Join the annotations with the original tasks and compute metrics by model."""

import argparse
import logging
import pathlib
import sys
import yaml
import random

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
    parser.add_argument(
        "--annotations_file",
        type=str,
        help="The name of the annotations file.",
        required=False,
    )
    parser.add_argument(
        "--output_format",
        type=str,
        default="yaml",
        help="The type of output files.",
        required=False,
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=0,
        help="Number of samples to include in yaml output.",
        required=False,
    )
    return parser.parse_args()

def main():
    args = get_arguments()
    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    model_outputs = pathlib.Path(args.model_outputs)
    annotations = pathlib.Path(args.annotations_file)
    annotation_docs = yaml.load_all(annotations.read_text(), Loader=yaml.Loader)
    labels = {}
    all_label_values = set({})
    for doc in annotation_docs:
        try:
            label = doc["label"][0]
        except IndexError as err:
            _LOGGER.info(f"Error extracting label from doc: {doc}: {err}")
            raise err

        labels[doc["uuid"]] = label
        all_label_values.add(label)
    all_label_values.add("Unavailable")

    model_results = {}
    model_samples = {}

    output_files = model_outputs.glob("**/*.yaml")
    for output_file in output_files:
        stem = output_file.relative_to(model_outputs)

        model_id = str(list(stem.parents)[0])
        if model_id not in model_results:
            model_results[model_id] = {}
            model_samples[model_id] = {}

        tasks = yaml.load_all(output_file.read_text(), Loader=yaml.Loader)
        for task in tasks:
            uid = task["uuid"]
            label = labels.get(uid, "Unavailable")
            model_results[model_id][label] = model_results[model_id].get(label, 0) + 1
            if not label in model_samples[model_id]:
                model_samples[model_id][label] = []
            if args.samples and "task" in task:
                model_samples[model_id][label].append(task["task"]["input_text"])

    if args.output_format == "yaml":
        print(yaml.dump(model_results, sort_keys=True, explicit_start=True))

        if args.samples:
            limited_samples = {}
            for model_id in model_samples:
                limited_samples[model_id] = {}
                for label in model_samples[model_id]:
                    samples = model_samples[model_id][label]
                    if len(samples) > args.samples:
                        samples = random.sample(samples, args.samples)
                    limited_samples[model_id][label] = samples
            print(yaml.dump(limited_samples, sort_keys=True, explicit_start=True))
    else:
        cols = sorted(list(all_label_values))
        print(",".join(["model"] + cols))
        for model_id, label_dict in model_results.items():
            row = []
            row.append(model_id)
            row.extend([
                str(label_dict.get(col, 0))
                for col in cols
            ])
            print(",".join(row))


if __name__ == "__main__":
    main()
