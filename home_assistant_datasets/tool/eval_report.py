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

from home_assistant_datasets.tool.data_model import EvalMetric


_LOGGER = logging.getLogger(__name__)

GOOD_LABEL = "Good"
BAD_LABEL = "Bad"
REPORT_FILE = "report.yaml"
REPORT_DETAIL_FILE = "report.csv"
IGNORE_CSV_COLS = {"uuid", "task_id", "context"}


class EvalReport:
    """Class for wriing the summarized eval metric results."""

    def __init__(self, model_output_dir: pathlib.Path) -> None:
        """Initialize report."""
        self._report_file = model_output_dir / REPORT_FILE
        self._eval_metrics: list[EvalMetric] = []

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: Any) -> None:
        """Invoked when all tests in the session have completed."""
        _LOGGER.debug("pytest_sessionfinish")
        report_doc = {
            "results": [
                dataclasses.asdict(eval_metric) for eval_metric in self._eval_metrics
            ]
        }
        report_doc_content = yaml.dump(report_doc, sort_keys=False, explicit_start=True)
        self._report_file.write_text(report_doc_content)

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter: Any) -> None:
        _LOGGER.debug("pytest_terminal_summary")
        terminalreporter.write_sep(
            "-",
            f"Generated eval report: {str(self._report_file)}",
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
        eval_metric.success = report.passed

        # Append to the results used when generating the final report
        self._eval_metrics.append(eval_metric)


class OutputType(enum.StrEnum):
    CSV = "csv"
    YAML = "yaml"
    REPORT = "report"


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
        print(
            yaml.dump(dataclasses.asdict(item), sort_keys=False, explicit_start=True),
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
            val = str(item_row[col])
            val = val.replace('"', "'")
            vals.append(f'"{val}"')
        print(",".join(vals), file=self._fd)


class ReportWriter(WriterBase):
    """Handles creation of an eval report."""

    def __init__(self, fd: io.TextIOBase) -> None:
        """Initialize ReportWriter."""
        self._fd = fd
        self.model_totals: dict[str, int] = {}
        self.model_good: dict[str, int] = {}

    def row(self, item: EvalMetric) -> None:
        """Handle a report row collecting the # of good labels for each model."""
        model_id = item.model_id
        if model_id not in self.model_totals:
            self.model_totals[model_id] = 0
            self.model_good[model_id] = 0
        self.model_totals[model_id] += 1
        if item.label == GOOD_LABEL:
            self.model_good[model_id] += 1

    def finish(self) -> None:
        """Print the report summary"""
        items = [
            {
                "model_id": model_id,
                "good_percent": f"{100*(self.model_good[model_id] / total):0.1f}%",
                "good": self.model_good[model_id],
                "total": total,
            }
            for model_id, total in self.model_totals.items()
        ]
        print(yaml.dump(items, sort_keys=False, explicit_start=True), file=self._fd)


def create_writer(
    output_type: OutputType, cls: EvalMetric, fd: io.TextIOBase | None = None
) -> WriterBase:
    """Create a writer for the output type."""
    if fd is None:
        fd = sys.stdout  # type: ignore[assignment]
        assert fd is not None
    if output_type == OutputType.CSV:
        return CsvWriter(
            [
                f.name
                for f in dataclasses.fields(cls)
                if f.name not in IGNORE_CSV_COLS
            ],
            fd,
        )
    if output_type == OutputType.YAML:
        return YamlWriter(fd)
    if output_type == OutputType.REPORT:
        return ReportWriter(fd)
    raise ValueError(f"Unknown output type: {output_type}")
