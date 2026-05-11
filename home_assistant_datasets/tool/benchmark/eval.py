"""Compute evaluation metrics from collected outputs.

```
usage: home-assistant-datasets benchmark eval [-h]
                                              [--dataset DATASET | --language {es,fr,de,nl}]
                                              [--parallel] [--dry-run]
```
"""

import argparse

from ._common import (
    add_common_args,
    build_eval_tasks,
    get_ha_version,
    get_output_dir,
    resolve_datasets,
    run_tasks,
)

__all__ = []


def create_arguments(parser: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    add_common_args(parser)


def run(args: argparse.Namespace) -> int:
    """Run the eval phase: compute metrics from collected outputs."""
    datasets = resolve_datasets(args)
    dry_run = args.dry_run
    parallel = getattr(args, "parallel", False)

    ha_version = get_ha_version()
    print(f"HA version: {ha_version}")
    print(f"Datasets: {', '.join(datasets)}")
    print(f"Parallel: {parallel}")
    print()

    tasks, skipped = build_eval_tasks(datasets, dry_run=dry_run)

    for ds_name in skipped:
        print(f"Skipping {ds_name}: no output at {get_output_dir(ds_name)}")
        print("  (Run 'script/benchmark collect' first)")

    # Pytest exit code 1 means "tests failed" which is expected for
    # benchmarks (the model didn't score 100%).  Only exit codes >= 2
    # (internal error, interrupted, usage error, no tests) are real failures.
    failures = run_tasks(
        tasks,
        parallel=parallel,
        dry_run=dry_run,
        accept_rc={0, 1},
        label="Evaluating",
    )

    if skipped:
        print(f"Skipped (no output): {', '.join(skipped)}")
    if failures:
        print(f"Failed datasets: {', '.join(failures)}")
        return 1
    print("All evaluations completed successfully.")
    return 0
