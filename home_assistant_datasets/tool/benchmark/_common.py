"""Shared utilities for the benchmark subcommands."""

from __future__ import annotations

import argparse
import io
import pathlib
import re
import subprocess
import sys
import tempfile
import time

from home_assistant_datasets.tool.leaderboard.config import (
    ASSIST_FAMILY_DATASETS,
    DATASETS,
    LANGUAGES,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
DATASETS_DIR = REPO_ROOT / "datasets"
REPORTS_DIR = REPO_ROOT / "reports"

# Build the full set of assist-family dataset names (including multilingual)
_ASSIST_FAMILY_SET: set[str] = set(ASSIST_FAMILY_DATASETS) | {
    f"{ds}-{lang}" for ds in ASSIST_FAMILY_DATASETS for lang in LANGUAGES
}


def classify_dataset(name: str) -> str:
    """Return 'assist' or 'automations' based on the dataset name."""
    if name in _ASSIST_FAMILY_SET:
        return "assist"
    return "automations"


def resolve_datasets(args: argparse.Namespace) -> list[str]:
    """Return the list of dataset names to operate on based on CLI flags."""
    dataset = getattr(args, "dataset", None)
    language = getattr(args, "language", None)

    if dataset:
        return [dataset]
    if language:
        return [f"{ds}-{language}" for ds in DATASETS]
    return list(DATASETS)


def get_ha_version() -> str:
    """Get the installed Home Assistant version."""
    try:
        from importlib.metadata import version

        return version("homeassistant")
    except Exception:
        return "dev"


def get_output_dir(dataset_name: str) -> pathlib.Path:
    """Get the report output directory for a dataset."""
    return REPORTS_DIR / dataset_name / get_ha_version()


def run_pytest(pytest_args: list[str], *, dry_run: bool = False) -> int:
    """Run pytest as a subprocess, return exit code."""
    cmd = [sys.executable, "-m", "pytest"] + pytest_args
    cmd_str = " ".join(cmd)
    if dry_run:
        print(f"  [dry-run] {cmd_str}")
        return 0
    print(f"  Running: {cmd_str}")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return result.returncode


def _read_progress(log_file: pathlib.Path) -> str:
    """Read the last pytest progress percentage from a log file."""
    try:
        with open(log_file, "r") as f:
            # Read from end to find the last progress line efficiently
            f.seek(0, io.SEEK_END)
            size = f.tell()
            # Read last 4KB (enough to find the last progress line)
            f.seek(max(0, size - 4096))
            tail = f.read()
        # Pytest outputs lines like: "test_name PASSED  [ 42%]"
        matches = re.findall(r"\[\s*(\d+)%\]", tail)
        if matches:
            return f"{matches[-1]}%"
    except OSError:
        pass
    return "..."


def run_datasets_parallel(
    dataset_tasks: list[tuple[str, list[str]]],
    *,
    dry_run: bool = False,
    accept_rc: set[int] | None = None,
) -> list[str]:
    """Run multiple pytest invocations in parallel.

    Returns list of failed dataset names. Exit codes in accept_rc are
    treated as success (default: {0}).
    """
    if accept_rc is None:
        accept_rc = {0}
    if dry_run:
        for ds_name, pytest_args in dataset_tasks:
            cmd = [sys.executable, "-m", "pytest"] + pytest_args
            print(f"  [dry-run] [parallel] {ds_name}: {' '.join(cmd)}")
        return []

    log_dir = pathlib.Path(tempfile.mkdtemp(prefix="benchmark-"))

    # Launch all processes
    running: list[tuple[str, subprocess.Popen, pathlib.Path, io.TextIOWrapper]] = []
    for ds_name, pytest_args in dataset_tasks:
        cmd = [sys.executable, "-m", "pytest"] + pytest_args
        log_file = log_dir / f"{ds_name}.log"
        fh = open(log_file, "w")
        proc = subprocess.Popen(
            cmd, cwd=str(REPO_ROOT), stdout=fh, stderr=subprocess.STDOUT
        )
        running.append((ds_name, proc, log_file, fh))

    total = len(running)
    is_tty = sys.stdout.isatty()

    # Poll for completion, showing live progress
    completed = 0
    failures: list[str] = []
    results: dict[str, str] = {}
    remaining = list(running)
    prev_lines = 0

    while remaining:
        still_running = []
        for ds_name, proc, log_file, fh in remaining:
            if proc.poll() is not None:
                fh.close()
                completed += 1
                status = "OK" if proc.returncode in accept_rc else "FAILED"
                results[ds_name] = status
                if proc.returncode not in accept_rc:
                    failures.append(ds_name)
            else:
                still_running.append((ds_name, proc, log_file, fh))
        remaining = still_running

        # Build status display
        lines: list[str] = []
        for ds_name, _, log_file, _ in running:
            if ds_name in results:
                lines.append(f"  {results[ds_name]:>6}  {ds_name}")
            else:
                pct = _read_progress(log_file)
                lines.append(f"  {pct:>6}  {ds_name}")
        header = f"  [{completed}/{total} done]"
        display = header + "\n" + "\n".join(lines)

        if is_tty:
            # Move cursor up to overwrite previous output
            if prev_lines > 0:
                sys.stdout.write(f"\033[{prev_lines}A\033[J")
            sys.stdout.write(display + "\n")
            sys.stdout.flush()
            prev_lines = display.count("\n") + 1
        elif completed > (total - len(remaining)):
            # Non-TTY: only print when something finishes
            print(display)

        if remaining:
            time.sleep(1)

    # Final summary (non-TTY or to ensure it's visible)
    if not is_tty:
        print(f"\n  [{completed}/{total} done]")
        for ds_name, _, log_file, _ in running:
            print(f"  {results[ds_name]:>6}  {ds_name} (log: {log_file})")

    # Always print log paths
    if is_tty:
        print()
    print(f"  Logs: {log_dir}")

    return failures


def validate_dataset_dir(dataset_name: str) -> None:
    """Check that a dataset directory exists."""
    ds_dir = DATASETS_DIR / dataset_name
    if not ds_dir.is_dir():
        die(f"Dataset directory not found: {ds_dir}")


def validate_model(model_id: str) -> None:
    """Check that a model config exists."""
    model_dir = REPO_ROOT / "models"
    model_file = model_dir / f"{model_id}.yaml"
    if not model_file.is_file():
        # Also check subdirectories
        matches = list(model_dir.rglob(f"{model_id}.yaml"))
        if not matches:
            die(f"Model config not found: models/{model_id}.yaml")


def die(msg: str) -> None:
    """Print error and exit."""
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def build_collect_tasks(
    datasets: list[str], model: str, *, dry_run: bool = False
) -> list[tuple[str, list[str]]]:
    """Build (dataset_name, pytest_args) tuples for the collect phase."""
    tasks: list[tuple[str, list[str]]] = []
    for ds_name in datasets:
        output_dir = get_output_dir(ds_name)
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)

        family = classify_dataset(ds_name)
        if family == "assist":
            test_dir = "home_assistant_datasets/tool/assist/collect"
        else:
            test_dir = "home_assistant_datasets/tool/automation/collect"

        pytest_args = [
            test_dir,
            f"--models={model}",
            f"--dataset=datasets/{ds_name}/",
            f"--model_output_dir={output_dir}",
        ]
        tasks.append((ds_name, pytest_args))
    return tasks


def build_eval_tasks(
    datasets: list[str], *, dry_run: bool = False
) -> tuple[list[tuple[str, list[str]]], list[str]]:
    """Build (dataset_name, pytest_args) tuples for the eval phase.

    Returns (tasks, skipped) where skipped are datasets with no output dir.
    """
    tasks: list[tuple[str, list[str]]] = []
    skipped: list[str] = []
    for ds_name in datasets:
        output_dir = get_output_dir(ds_name)
        if not output_dir.exists() and not dry_run:
            skipped.append(ds_name)
            continue

        family = classify_dataset(ds_name)
        if family == "assist":
            pytest_args = [
                "home_assistant_datasets/tool/assist/eval",
                f"--model_output_dir={output_dir}",
            ]
        else:
            pytest_args = [
                f"datasets/{ds_name}/",
                f"--model_output_dir={output_dir}",
            ]
        tasks.append((ds_name, pytest_args))
    return tasks, skipped


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add dataset/language selection and common flags to a subcommand parser."""
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dataset",
        help="Run a specific dataset (e.g., assist-es, automations)",
    )
    group.add_argument(
        "--language",
        choices=LANGUAGES,
        help="Run all datasets for a language (e.g., es)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run all datasets in parallel (output goes to log files)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them",
    )
