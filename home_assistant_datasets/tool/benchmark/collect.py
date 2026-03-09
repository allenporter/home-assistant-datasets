"""Collect model outputs against datasets.

```
usage: home-assistant-datasets benchmark collect [-h] --model MODEL
                                                 [--dataset DATASET | --language {es,fr,de,nl}]
                                                 [--synthetic-home-dir DIR]
                                                 [--parallel] [--dry-run]
```
"""

import argparse

from ._common import (
    add_common_args,
    build_collect_tasks,
    build_env,
    classify_dataset,
    find_synthetic_home,
    get_ha_version,
    resolve_datasets,
    run_datasets_parallel,
    run_pytest,
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
    synthetic_home = find_synthetic_home(args)
    env = build_env(synthetic_home)
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
    print(f"Synthetic home: {synthetic_home}")
    print(f"Parallel: {parallel}")
    print()

    tasks = build_collect_tasks(datasets, model, dry_run=dry_run)

    if parallel and len(tasks) > 1:
        failures = run_datasets_parallel(tasks, env, dry_run=dry_run)
    else:
        failures = []
        for ds_name, pytest_args in tasks:
            print(f"{'=' * 60}")
            print(f"Collecting: {ds_name} (family={classify_dataset(ds_name)})")
            print(f"{'=' * 60}")
            rc = run_pytest(pytest_args, env, dry_run=dry_run)
            if rc != 0:
                failures.append(ds_name)
                print(f"  FAILED: {ds_name}")
            print()

    if failures:
        print(f"Failed datasets: {', '.join(failures)}")
        return 1
    print("All collections completed successfully.")
    return 0
