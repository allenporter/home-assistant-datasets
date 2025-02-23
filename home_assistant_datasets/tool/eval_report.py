"""Generates reports summarizing evaluation metrics from pytest results."""

import pathlib
import dataclasses
import logging

import pytest
import yaml

from home_assistant_datasets.tool.data_model import EvalMetric

_LOGGER = logging.getLogger(__name__)

REPORT_FILE = "report.yaml"
REPORT_DETAIL_FILE = "report.csv"


class EvalReport:
    """Class for wriing the summarized eval metric results."""

    def __init__(self, model_output_dir: pathlib.Path) -> None:
        """Initialize report."""
        self._report_file = model_output_dir / REPORT_FILE
        self._eval_metrics: list[EvalMetric] = []

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session):
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
    def pytest_terminal_summary(self, terminalreporter):
        _LOGGER.debug("pytest_terminal_summary")
        terminalreporter.write_sep(
            "-",
            f"Generated eval report: {str(self._report_file)}",
        )

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report):
        """Invoked at the completion of a test run."""
        _LOGGER.debug("pytest_runtest_logreport: %s %s", report.when, report.outcome)
        assert report.outcome != "rerun", "Rerun not supported"
        if report.when != "call":  # Ignore setup and teardown
            return
        if report.eval_metric is None:
            raise ValueError("Unable to run eval report with missing Eval Metric fixture")
            return

        # Record the test failure in the eval metric
        eval_metric = report.eval_metric
        eval_metric.success = report.passed

        # Append to the results used when generating the final report
        self._eval_metrics.append(eval_metric)
