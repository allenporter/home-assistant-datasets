"""Module for building an entire suite of reports."""

from dataclasses import dataclass
import io
import logging
import pathlib
from collections.abc import Callable
from typing import TypeVar, Any


from . import TaskResult, ScrapeRecord
from .accuracy import AccuracySummary
from .report import ScrapeRecordWriter, TaskResultWriter
from .report_csv import create_csv_writer
from .token_stats import ModelTokenStats

__all__ = [
    "ReportSuiteConfig",
    "ReportSuite",
    "exception_repr",
]

_LOGGER = logging.getLogger(__name__)
_T = TypeVar("_T", bound=ScrapeRecordWriter | TaskResultWriter)


def create_model_accuracy(fd: io.TextIOBase | None) -> AccuracySummary:
    """Create an accuracy summary report aggregated by model id."""
    return AccuracySummary(fd, summary_key="model_id")


def create_task_id_accuracy(fd: io.TextIOBase | None) -> AccuracySummary:
    """Create an accuracy summary report aggregated by model id."""
    return AccuracySummary(fd, summary_key="task_id")


def create_test_name_accuracy(fd: io.TextIOBase | None) -> AccuracySummary:
    """Create an accuracy summary report aggregated by model id."""
    return AccuracySummary(fd, summary_key="task_name")

def create_category_accuracy(fd: io.TextIOBase | None) -> AccuracySummary:
    """Create an accuracy summary report aggregated by model id."""
    return AccuracySummary(fd, summary_key="category")

def create_model_token_stats(fd: io.TextIOBase | None) -> ScrapeRecordWriter:
    """Create an accuracy summary report aggregated by model id."""
    return ModelTokenStats(fd)


def create_model_test_name_accuracy(fd: io.TextIOBase | None) -> AccuracySummary:
    """Create an accuracy summary report aggregated by model id."""
    return AccuracySummary(fd, summary_key=["model_id", "task_name"])


def create_model_category_accuracy(fd: io.TextIOBase | None) -> AccuracySummary:
    """Create an accuracy summary report aggregated by model id."""
    return AccuracySummary(fd, summary_key=["model_id", "category"])


DEFAULT_SCRAPE_REPORTS: list[tuple[str, Callable[[Any], ScrapeRecordWriter]]] = [
    ("reports-token-stats.yaml", create_model_token_stats),
]

DEFAULT_TASK_REPORTS: list[tuple[str, Callable[[Any], TaskResultWriter]]] = [
    ("reports.yaml", create_model_accuracy),
    ("reports-by-model-test-name.yaml", create_model_test_name_accuracy),
    ("reports-by-model-category.yaml", create_model_category_accuracy),
    ("reports-by-test-name.yaml", create_test_name_accuracy),
    ("reports-by-task-id.yaml", create_task_id_accuracy),
    ("reports-by-category.yaml", create_category_accuracy),
    ("report.csv", create_csv_writer),
]


@dataclass
class ReportSuiteConfig:
    """Configuration for the evaluation report."""

    output_dir: pathlib.Path
    """Path to output metrics."""


class ReportSuite:
    """An entire suite of evaluation metrics."""

    def __init__(self, config: ReportSuiteConfig) -> None:
        """Initialize ReportSuite."""
        self._config = config
        self._result_writers: list[TaskResultWriter] = []
        self._scrape_writers: list[ScrapeRecordWriter] = []
        self._file_paths: list[pathlib.Path] = []
        self._fd: list[io.TextIOBase] = []

    def _create_writer(
        self,
        report_file: str,
        report_fn: Callable[[io.TextIOBase], _T],
    ) -> _T:
        file_path = self._config.output_dir / report_file
        _LOGGER.debug("Creating report file: %s", file_path)
        self._file_paths.append(file_path)
        fd = file_path.open("w")
        self._fd.append(fd)
        writer = report_fn(fd)
        writer.start()
        return writer

    def open(self) -> None:
        """Open the report files for writing."""
        if not self._config.output_dir.exists():
            raise ValueError(
                f"Model output directory does not exist: {str(self._config.output_dir)}",
            )

        for report_file, scrape_fn in DEFAULT_SCRAPE_REPORTS:
            self._scrape_writers.append(self._create_writer(report_file, scrape_fn))

        for report_file, task_fn in DEFAULT_TASK_REPORTS:
            self._result_writers.append(self._create_writer(report_file, task_fn))

    def scrape_record(self, scrape: ScrapeRecord) -> None:
        """Record the task results in the report."""
        _LOGGER.debug("scrape_record=%s", scrape)
        for writer in self._scrape_writers:
            writer.row(scrape)

    def task_result(self, scrape: ScrapeRecord, result: TaskResult) -> None:
        """Record the task results in the report."""
        for writer in self._result_writers:
            writer.row(scrape, result)

    def finish(self) -> None:
        """Close the report files and flush contents."""
        for sc_writer in self._scrape_writers:
            sc_writer.finish()
        for r_writer in self._result_writers:
            r_writer.finish()
        for fd in self._fd:
            fd.close()

    @property
    def report_paths(self) -> list[str]:
        """Return the set of output report file paths."""
        return [str(report_file) for report_file in self._file_paths]


def exception_repr(longreprtext: str) -> str:
    """Return an exception message from a pytest longreprtext."""
    lines = longreprtext.split("\n")
    excs: list[str] = []
    for line in lines:
        if line.startswith("E   "):
            excs.append(line[4:].lstrip())
    if excs:
        return ",".join(excs[-2:])
    return longreprtext


def extract_task_name(node_id: str) -> str:
    """Extract a task id from the test filename.

    We can use the path and test name as the task id since it is more
    descriptive than the original problem name used as a task.
    For a nodeid like:
        datasets/automations/light_on_door/test_blueprint.py::test_light_timeout[..../]
    We want a task id of `light_on_door-test_light_timeout`
    """
    node_parts = node_id.split("::")
    path_parts = node_parts[0].split("/")
    if len(path_parts) == 1:  # No path component
        task_prefix = path_parts[-1]
    else:
        task_prefix = path_parts[-2]
    test_method = node_parts[-1].split("[")[0]
    return "-".join([task_prefix, test_method])
