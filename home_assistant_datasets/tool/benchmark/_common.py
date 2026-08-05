"""Shared utilities for the benchmark subcommands."""

from __future__ import annotations

from abc import ABC, abstractmethod
import argparse
from dataclasses import dataclass
import io
from importlib.metadata import PackageNotFoundError, version
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

# Pytest writes progress lines like: "test_name PASSED  [ 42%]"
_PROGRESS_RE = re.compile(r"\[\s*(\d+)%\]")

# Number of bytes read from the end of a log file to find the last progress line
_PROGRESS_TAIL_BYTES = 4096

# Seconds to wait between status updates while tasks are running
_POLL_INTERVAL = 1.0

_TABLE_WIDTH = 60

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


def resolve_concurrency(args: argparse.Namespace, num_datasets: int) -> int:
    """Return the maximum number of datasets to run at the same time.

    A bare `--parallel` flag means every dataset at once, otherwise the
    value passed to `--parallel` is the upper bound (default: one at a time).
    """
    parallel = getattr(args, "parallel", 1)
    if parallel is None or parallel <= 0:
        return max(1, num_datasets)
    return max(1, min(parallel, num_datasets))


def get_ha_version() -> str:
    """Get the installed Home Assistant version."""
    try:
        return version("homeassistant")
    except PackageNotFoundError:
        return "dev"


def get_output_dir(dataset_name: str) -> pathlib.Path:
    """Get the report output directory for a dataset."""
    return REPORTS_DIR / dataset_name / get_ha_version()


def validate_dataset_dir(dataset_name: str) -> None:
    """Check that a dataset directory exists.

    Raises ValueError if the dataset directory does not exist.
    """
    ds_dir = DATASETS_DIR / dataset_name
    if not ds_dir.is_dir():
        raise ValueError(f"Dataset directory not found: {ds_dir}")


def validate_model(model_id: str) -> None:
    """Check that a model config exists.

    Raises ValueError if no model configuration file can be found.
    """
    model_dir = REPO_ROOT / "models"
    if (model_dir / f"{model_id}.yaml").is_file():
        return
    # Also check subdirectories
    if not list(model_dir.rglob(f"{model_id}.yaml")):
        raise ValueError(f"Model config not found: models/{model_id}.yaml")


@dataclass
class Task:
    """A single pytest invocation for one dataset."""

    dataset: str
    """Name of the dataset this task operates on."""

    pytest_args: list[str]
    """Arguments passed to pytest."""

    @property
    def command(self) -> list[str]:
        """The command line used to run this task."""
        return [sys.executable, "-m", "pytest", *self.pytest_args]


@dataclass
class _RunningTask:
    """A task that has been started as a subprocess."""

    task: Task
    process: subprocess.Popen
    log_file: pathlib.Path | None = None
    log_handle: io.TextIOWrapper | None = None

    def progress(self) -> str:
        """Return the last pytest progress percentage reported by the task."""
        if self.log_file is None:
            return "..."
        return _read_progress(self.log_file)

    def close(self) -> None:
        """Release the log file handle."""
        if self.log_handle is not None:
            self.log_handle.close()
            self.log_handle = None


def _read_progress(log_file: pathlib.Path) -> str:
    """Read the last pytest progress percentage from a log file."""
    try:
        with log_file.open("r") as f:
            # Read from end to find the last progress line efficiently
            f.seek(0, io.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - _PROGRESS_TAIL_BYTES))
            tail = f.read()
    except OSError:
        return "..."
    if matches := _PROGRESS_RE.findall(tail):
        return f"{matches[-1]}%"
    return "..."


class StatusWriter(ABC):
    """Base class for reporting the status of benchmark tasks."""

    @abstractmethod
    def task_started(self, task: Task, *, dry_run: bool) -> None:
        """Write that a task has started."""

    @abstractmethod
    def task_finished(self, task: Task, returncode: int, *, ok: bool) -> None:
        """Write that a task has exited."""

    @abstractmethod
    def status(self, rows: list[tuple[str, str]], completed: int, total: int) -> None:
        """Write the status of every task, called while tasks are running."""

    @abstractmethod
    def finish(self, log_dir: pathlib.Path | None) -> None:
        """Write the output summary."""


class StreamStatusWriter(StatusWriter):
    """Status writer for tasks that stream their output to the console.

    Used when tasks run one at a time (or for a dry run), where pytest itself
    writes progress to the console so there is nothing to poll.
    """

    def __init__(self, label: str) -> None:
        """Initialize StreamStatusWriter."""
        self._label = label

    def task_started(self, task: Task, *, dry_run: bool) -> None:
        """Write that a task has started."""
        print("=" * _TABLE_WIDTH)
        print(
            f"{self._label}: {task.dataset} (family={classify_dataset(task.dataset)})"
        )
        print("=" * _TABLE_WIDTH)
        prefix = "[dry-run]" if dry_run else "Running:"
        print(f"  {prefix} {' '.join(task.command)}")

    def task_finished(self, task: Task, returncode: int, *, ok: bool) -> None:
        """Write that a task has exited."""
        if not ok:
            print(f"  FAILED: {task.dataset} (exit code {returncode})")
        print()

    def status(self, rows: list[tuple[str, str]], completed: int, total: int) -> None:
        """Write the status of every task, already covered by pytest output."""

    def finish(self, log_dir: pathlib.Path | None) -> None:
        """Write the output summary."""


class TableStatusWriter(StatusWriter):
    """Base status writer for tasks that write their output to log files."""

    def task_started(self, task: Task, *, dry_run: bool) -> None:
        """Write that a task has started, shown in the status table instead."""

    def task_finished(self, task: Task, returncode: int, *, ok: bool) -> None:
        """Write that a task has exited, shown in the status table instead."""

    def finish(self, log_dir: pathlib.Path | None) -> None:
        """Write the output summary."""
        if log_dir is not None:
            print(f"  Logs: {log_dir}")

    def _render(self, rows: list[tuple[str, str]], completed: int, total: int) -> str:
        """Render the status of every task as a table."""
        lines = [f"  [{completed}/{total} done]"]
        lines.extend(f"  {status:>7}  {name}" for name, status in rows)
        return "\n".join(lines)


class TTYStatusWriter(TableStatusWriter):
    """Status writer that redraws the status table in place on a terminal."""

    def __init__(self) -> None:
        """Initialize TTYStatusWriter."""
        self._prev_lines = 0

    def status(self, rows: list[tuple[str, str]], completed: int, total: int) -> None:
        """Write the status of every task, overwriting the previous table."""
        display = self._render(rows, completed, total)
        if self._prev_lines:
            # Move the cursor up and erase the previously written table
            sys.stdout.write(f"\033[{self._prev_lines}A\033[J")
        sys.stdout.write(display + "\n")
        sys.stdout.flush()
        self._prev_lines = display.count("\n") + 1

    def finish(self, log_dir: pathlib.Path | None) -> None:
        """Write the output summary."""
        print()
        super().finish(log_dir)


class PlainStatusWriter(TableStatusWriter):
    """Status writer that prints the status table when a task finishes."""

    def __init__(self) -> None:
        """Initialize PlainStatusWriter."""
        self._completed = -1

    def status(self, rows: list[tuple[str, str]], completed: int, total: int) -> None:
        """Write the status of every task when the completed count changes."""
        if completed == self._completed:
            return
        self._completed = completed
        print(self._render(rows, completed, total))


def create_status_writer(label: str, *, capture: bool) -> StatusWriter:
    """Create the status writer to use for the current console."""
    if not capture:
        return StreamStatusWriter(label)
    if sys.stdout.isatty():
        return TTYStatusWriter()
    return PlainStatusWriter()


def _start_task(task: Task, log_dir: pathlib.Path | None) -> _RunningTask:
    """Start a task as a subprocess, writing to a log file when capturing."""
    if log_dir is None:
        return _RunningTask(
            task=task, process=subprocess.Popen(task.command, cwd=str(REPO_ROOT))
        )
    log_file = log_dir / f"{task.dataset}.log"
    log_handle = log_file.open("w")
    process = subprocess.Popen(
        task.command,
        cwd=str(REPO_ROOT),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
    )
    return _RunningTask(
        task=task, process=process, log_file=log_file, log_handle=log_handle
    )


def run_tasks(
    tasks: list[Task],
    *,
    max_concurrency: int = 1,
    dry_run: bool = False,
    accept_rc: set[int] | None = None,
    label: str = "Running",
) -> list[str]:
    """Run tasks with at most `max_concurrency` of them running at once.

    Returns the list of failed dataset names. Exit codes in `accept_rc` are
    treated as success (default: {0}).
    """
    if accept_rc is None:
        accept_rc = {0}
    if not tasks:
        return []

    concurrency = 1 if dry_run else max(1, min(max_concurrency, len(tasks)))
    # A single task at a time writes straight to the console. Concurrent tasks
    # would interleave their output, so it is captured in log files and the
    # console shows a status table instead.
    capture = concurrency > 1
    log_dir = pathlib.Path(tempfile.mkdtemp(prefix="benchmark-")) if capture else None
    writer = create_status_writer(label, capture=capture)

    pending = list(tasks)
    running: dict[str, _RunningTask] = {}
    finished: dict[str, str] = {}
    failures: list[str] = []

    while pending or running:
        while pending and len(running) < concurrency:
            task = pending.pop(0)
            writer.task_started(task, dry_run=dry_run)
            if dry_run:
                finished[task.dataset] = "OK"
                writer.task_finished(task, 0, ok=True)
                continue
            running[task.dataset] = _start_task(task, log_dir)

        for item in [
            item for item in running.values() if item.process.poll() is not None
        ]:
            del running[item.task.dataset]
            item.close()
            returncode = item.process.returncode
            ok = returncode in accept_rc
            finished[item.task.dataset] = "OK" if ok else "FAILED"
            if not ok:
                failures.append(item.task.dataset)
            writer.task_finished(item.task, returncode, ok=ok)

        writer.status(
            [(task.dataset, _task_status(task, finished, running)) for task in tasks],
            len(finished),
            len(tasks),
        )
        if running:
            time.sleep(_POLL_INTERVAL)

    writer.finish(log_dir)
    return failures


def _task_status(
    task: Task, finished: dict[str, str], running: dict[str, _RunningTask]
) -> str:
    """Return the status text to display for a task."""
    if (status := finished.get(task.dataset)) is not None:
        return status
    if (item := running.get(task.dataset)) is not None:
        return item.progress()
    return "queued"


def build_collect_tasks(
    datasets: list[str], model: str, *, dry_run: bool = False
) -> list[Task]:
    """Build the list of tasks for the collect phase."""
    tasks: list[Task] = []
    for ds_name in datasets:
        output_dir = get_output_dir(ds_name)
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)

        family = classify_dataset(ds_name)
        if family == "assist":
            test_dir = "home_assistant_datasets/tool/assist/collect"
        else:
            test_dir = "home_assistant_datasets/tool/automation/collect"

        tasks.append(
            Task(
                dataset=ds_name,
                pytest_args=[
                    test_dir,
                    f"--models={model}",
                    f"--dataset=datasets/{ds_name}/",
                    f"--model_output_dir={output_dir}",
                ],
            )
        )
    return tasks


def build_eval_tasks(
    datasets: list[str], *, dry_run: bool = False
) -> tuple[list[Task], list[str]]:
    """Build the list of tasks for the eval phase.

    Returns (tasks, skipped) where skipped are datasets with no output dir.
    """
    tasks: list[Task] = []
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
        tasks.append(Task(dataset=ds_name, pytest_args=pytest_args))
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
        nargs="?",
        type=int,
        const=0,
        default=1,
        metavar="N",
        help=(
            "Maximum number of datasets to run at the same time, or every "
            "dataset at once when no value is given (default: 1). Output of "
            "concurrent datasets goes to log files."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them",
    )
