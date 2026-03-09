"""Collect model outputs against datasets.

```
usage: home-assistant-datasets benchmark collect [-h] --model MODEL
                                                 [--dataset DATASET | --language {es,fr,de,nl}]
                                                 [--parallel] [--dry-run]
```
"""

import argparse

from ._common import (
    add_common_args,
    build_collect_tasks,
    get_ha_version,
    resolve_datasets,
    run_tasks,
    validate_dataset_dir,
    validate_model,
)

__all__ = []


def create_arguments(parser: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    parser.add_argument(
        "--model", required=True, help="Model ID to evaluate (e.g., devstral-2512)"
    )
    add_common_args(parser)


def run(args: argparse.Namespace) -> int:
    """Run the collect phase: scrape model outputs for datasets."""
    datasets = resolve_datasets(args)
    model = args.model
    dry_run = args.dry_run
    parallel = getattr(args, "parallel", False)

    validate_model(model)
    for ds in datasets:
        validate_dataset_dir(ds)

    ha_version = get_ha_version()
    print(f"Model: {model}")
    print(f"HA version: {ha_version}")
    print(f"Datasets: {', '.join(datasets)}")
    print(f"Parallel: {parallel}")
    print()

    tasks = build_collect_tasks(datasets, model, dry_run=dry_run)
    failures = run_tasks(tasks, parallel=parallel, dry_run=dry_run, label="Collecting")

    if failures:
        print(f"Failed datasets: {', '.join(failures)}")
        return 1
    print("All collections completed successfully.")
    return 0
