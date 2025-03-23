"""Generates reports summarizing evaluation metrics from pytest results."""

import enum
import dataclasses
import logging
import pathlib
import io
import sys
from typing import Any

import pytest
import yaml

from home_assistant_datasets.tool.data_model import (
    EvalMetric,
    TokenStatsBank,
)


_LOGGER = logging.getLogger(__name__)

GOOD_LABEL = "Good"
BAD_LABEL = "Bad"
REPORT_FILE = "reports.yaml"
REPORT_DETAIL_FILE = "report.csv"
IGNORE_CSV_COLS = {"uuid", "context", "token_stats", "duration_ms"}
SUMMARY_KEYS = {"model_id", "task_id"}


class OutputType(enum.StrEnum):
    CSV = "csv"
    YAML = "yaml"
    REPORT = "report"


DEFAULT_REPORTS = [
    ("reports.yaml", OutputType.REPORT, "model_id"),
    ("reports-by-task.yaml", OutputType.REPORT, "task_id"),
    ("report.csv", OutputType.CSV, None),
]


class EvalReport:
    """Class for wriing the summarized eval metric results."""

    def __init__(self, model_output_dir: pathlib.Path, cls: type[EvalMetric]) -> None:
        """Initialize report."""
        self._model_output_dir = model_output_dir
        self._cls = cls
        self._writers: list[WriterBase] = []
        self._file_paths: list[pathlib.Path] = []
        self._fd: list[io.TextIOBase] = []

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session: Any) -> None:
        """Invoked at the start of the session."""
        if not self._model_output_dir.exists():
            raise ValueError(
                f"Model output directory does not exist: {self._model_output_dir}"
            )

        for report_file, output_type, summary_key in DEFAULT_REPORTS:
            file_path = self._model_output_dir / report_file
            _LOGGER.debug("Creating report file: %s", file_path)
            self._file_paths.append(file_path)
            fd = file_path.open("w")
            self._fd.append(fd)
            writer = create_writer(output_type, self._cls, fd, summary_key)
            writer.start()
            self._writers.append(writer)

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: Any) -> None:
        """Invoked when all tests in the session have completed."""
        _LOGGER.debug("pytest_sessionfinish")
        for writer in self._writers:
            writer.finish()
        for fd in self._fd:
            fd.close()

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter: Any) -> None:
        _LOGGER.debug("pytest_terminal_summary")
        for report_file in self._file_paths:
            terminalreporter.write_sep(
                "-",
                f"Generated eval report: {str(report_file)}",
            )

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report: Any) -> None:
        """Invoked at the completion of a test run."""
        _LOGGER.debug("pytest_runtest_logreport: %s %s", report.when, report.outcome)
        assert report.outcome != "rerun", "Rerun not supported"
        if report.when != "call":  # Ignore setup and teardown
            return
        if (eval_metric := getattr(report, "eval_metric")) is None:
            raise ValueError(
                "Unable to run eval report with missing Eval Metric fixture"
            )

        # Record the test failure in the eval metric
        eval_metric.label = GOOD_LABEL if report.passed else BAD_LABEL

        for writer in self._writers:
            writer.row(eval_metric)


def exception_repr(longreprtext: str) -> str:
    """Return the exception message from the longreprtext."""
    lines = longreprtext.split("\n")
    excs: list[str] = []
    for line in lines:
        if line.startswith("E   "):
            excs.append(line[4:].lstrip())
    if excs:
        return ",".join(excs[-2:])
    return longreprtext


class WriterBase:
    """Base class for eval output."""

    diff: type[dict] | type[str] = dict

    def start(self) -> None:
        """Write the output start."""

    def row(self, item: EvalMetric) -> None:
        """Write an output row."""

    def finish(self) -> None:
        """Write the output summary."""


class YamlWriter(WriterBase):
    """Eval output writer that"""

    def __init__(self, fd: io.TextIOBase) -> None:
        """Initialize the yaml writer."""
        self._fd = fd

    def row(self, item: EvalMetric) -> None:
        """Dump the record in yaml format."""
        record = dataclasses.asdict(item)
        non_empty = {k: v for k, v in record.items() if v is not None}
        print(
            yaml.dump(non_empty, sort_keys=False, explicit_start=True),
            file=self._fd,
        )


class CsvWriter(WriterBase):
    """Eval output writer that"""

    diff = str

    def __init__(self, cols: list[str], fd: io.TextIOBase) -> None:
        """Initialize the csv writer."""
        self._cols = cols
        self._fd = fd

    def start(self) -> None:
        """Write the csv header."""
        print(",".join(self._cols), file=self._fd)

    def row(self, item: EvalMetric) -> None:
        """Dump the record in csv format."""
        vals = []
        item_row = dataclasses.asdict(item)
        for col in self._cols:
            raw_value = item_row[col]
            val = str(raw_value) if raw_value is not None else ""
            val = val.replace('"', "'")
            val = val.replace("\n", "\\n")
            vals.append(f'"{val}"')
        print(",".join(vals), file=self._fd)


class DurationStats:
    """Class for duration statistics."""

    def __init__(self) -> None:
        """Initialize DurationStats."""
        self.durations: list[float] = []

    def append(self, duration: float) -> None:
        """Append a duration."""
        self.durations.append(duration)

    def total(self) -> float:
        """Return the total duration."""
        return sum(self.durations)

    def average(self) -> float:
        """Return the average duration."""
        return sum(self.durations) / len(self.durations)

    def min(self) -> float:
        """Return the minimum duration."""
        return min(self.durations)

    def max(self) -> float:
        """Return the maximum duration."""
        return max(self.durations)

    def summary_data(self) -> dict[str, Any]:
        """Return summary data."""
        return {
            "duration_ms": {
                "total": round(self.total(), 2),
                "avg": round(self.average(), 2),
                "min": round(self.min(), 2),
                "max": round(self.max(), 2),
            }
        }


class ReportWriter(WriterBase):
    """Handles creation of an eval report."""

    def __init__(self, fd: io.TextIOBase, summary_key: str) -> None:
        """Initialize ReportWriter."""
        self._fd = fd
        self.summary_key = summary_key
        self.totals: dict[str, int] = {}
        self.good: dict[str, int] = {}
        self.token_stats: dict[str, TokenStatsBank] = {}
        self.duration_stats: dict[str, DurationStats] = {}

    def row(self, item: EvalMetric) -> None:
        """Handle a report row collecting the # of good labels for each model."""
        key = getattr(item, self.summary_key)
        if key not in self.totals:
            self.totals[key] = 0
            self.good[key] = 0
        self.totals[key] += 1
        if item.label == GOOD_LABEL:
            self.good[key] += 1
        if item.token_stats:
            if key not in self.token_stats:
                self.token_stats[key] = TokenStatsBank()
            self.token_stats[key].append(item.token_stats)
        if item.duration_ms is not None:
            if key not in self.duration_stats:
                self.duration_stats[key] = DurationStats()
            self.duration_stats[key].append(item.duration_ms)

    def finish(self) -> None:
        """Print the report summary"""
        sorted_keys = sorted(self.totals.keys())

        items = []
        for key in sorted_keys:
            data = {
                self.summary_key: key,
                "good_percent": f"{100*(self.good[key] / self.totals[key]):0.1f}%",
                "good": self.good[key],
                "total": self.totals[key],
            }
            if token_stats := self.token_stats.get(key):
                data.update(token_stats.summary_data())
            if duration_stats := self.duration_stats.get(key):
                data.update(duration_stats.summary_data())
            items.append(data)
        print(yaml.dump(items, sort_keys=False, explicit_start=True), file=self._fd)


def create_writer(
    output_type: OutputType,
    cls: type[EvalMetric],
    fd: io.TextIOBase | None = None,
    summary_key: str | None = None,
) -> WriterBase:
    """Create a writer for the output type."""
    if fd is None:
        fd = sys.stdout  # type: ignore[assignment]
        assert fd is not None
    if output_type == OutputType.CSV:
        return CsvWriter(
            [f.name for f in dataclasses.fields(cls) if f.name not in IGNORE_CSV_COLS],
            fd,
        )
    if output_type == OutputType.YAML:
        return YamlWriter(fd)
    if output_type == OutputType.REPORT:
        if summary_key is None:
            summary_key = "model_id"
        return ReportWriter(fd, summary_key)
    raise ValueError(f"Unknown output type: {output_type}")
