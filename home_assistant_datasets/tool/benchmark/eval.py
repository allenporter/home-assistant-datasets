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
    classify_dataset,
    get_ha_version,
    get_output_dir,
    resolve_datasets,
    run_datasets_parallel,
    run_pytest,
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
    eval_accept_rc = {0, 1}

    if parallel and len(tasks) > 1:
        failures = run_datasets_parallel(
            tasks, dry_run=dry_run, accept_rc=eval_accept_rc
        )
    else:
        failures = []
        for ds_name, pytest_args in tasks:
            print(f"{'=' * 60}")
            print(f"Evaluating: {ds_name} (family={classify_dataset(ds_name)})")
            print(f"{'=' * 60}")
            rc = run_pytest(pytest_args, dry_run=dry_run)
            if rc not in eval_accept_rc:
                failures.append(ds_name)
                print(f"  FAILED: {ds_name} (exit code {rc})")
            else:
                output_dir = get_output_dir(ds_name)
                report_file = output_dir / "reports.yaml"
                if report_file.exists():
                    print(f"  Results: {report_file}")
            print()

    if skipped:
        print(f"Skipped (no output): {', '.join(skipped)}")
    if failures:
        print(f"Failed datasets: {', '.join(failures)}")
        return 1
    print("All evaluations completed successfully.")
    return 0
