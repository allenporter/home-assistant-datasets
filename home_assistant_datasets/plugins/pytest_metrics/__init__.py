"""Module for computing eval metrics from pytest.

This will run an evaluation using pytest to generate pass or fail, then
aggregate the results and writ ethem to an output file.

The requirements for this module are:
- Needs to know the output directory
- Needs to know the current "task" under test for report detail
- There may be multiple "tests" for each task (e.g. tone, accuracy, etc)
- Needs to get the success/failure for each test
- Write detailed metrics to a file
- Aggregate metrics e.g. by task, by model, etc and write outputs to a file

When using this fixture, your test is responsible for producing a
`scrape_record` fixture that produces a `@dataclass` of type
`home_assistant_datasets.metrics.report.ScrapeRecord`. This identifies the record
used by the output of a prior scrape run.

Each pytest test is an eval task. This plugin will examine the pytest output
and create a `home_assistant_datasets.metrics.report.TaskResult` that indicates
pass or failure.

This plugin handles writing out the report output.
"""

import logging
import pathlib
from typing import Any
from collections.abc import Generator

import pytest
from pytest import TestReport, Item, CallInfo, FixtureRequest, CollectReport

from home_assistant_datasets.metrics import (
    TaskResult,
    ScrapeRecord,
)
from home_assistant_datasets.metrics.report_suite import (
    ReportSuite,
    ReportSuiteConfig,
    exception_repr,
    extract_task_name,
)

__all__ = []

_LOGGER = logging.getLogger(__name__)

SUITE_STASH_KEY = pytest.StashKey[ReportSuite]
SCRAPE_RECORD_STASH_KEY = pytest.StashKey[ScrapeRecord]()


def pytest_addoption(parser: Any) -> None:
    """Pytest arguments passed."""
    parser.addoption("--model_output_dir", default=None)


def pytest_configure(config: Any) -> None:
    """Fixture to register the ReportSuitePlugin."""
    _LOGGER.debug("pytest_configure")
    model_output_dir = config.getoption("model_output_dir")
    suite = ReportSuite(
        ReportSuiteConfig(output_dir=pathlib.Path(model_output_dir)),
    )
    plugin = ReportSuitePlugin(
        suite,
    )
    config.pluginmanager.register(plugin)

    config.stash[SUITE_STASH_KEY] = suite


@pytest.fixture(name="consume_scrape_record", autouse=True, scope="module")
def scrape_record_fixture(
    request: FixtureRequest, scrape_record: ScrapeRecord
) -> Generator[None]:
    """Fixture to process the scrape record report."""
    report_suite = request.config.stash[SUITE_STASH_KEY]  # type: ignore[index]
    report_suite.scrape_record(scrape_record)

    # Hold on to the ScrapeRecord for info needed for computing/grouping the per-task results
    request.session.stash[SCRAPE_RECORD_STASH_KEY] = scrape_record
    yield
    del request.session.stash[SCRAPE_RECORD_STASH_KEY]


class ReportSuitePlugin:
    """Class for wriing the summarized eval metric results."""

    def __init__(self, suite: ReportSuite) -> None:
        """Initialize report."""
        self._suite = suite

    @pytest.hookimpl(trylast=True)
    def pytest_sessionstart(self, session: Any) -> None:
        """Invoked at the start of the session."""
        self._suite.open()

    @pytest.hookimpl(trylast=True)
    def pytest_sessionfinish(self, session: Any) -> None:
        """Invoked when all tests in the session have completed."""
        self._suite.finish()

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(
        self, item: Item, call: CallInfo[None]
    ) -> Generator[None, CollectReport, None]:
        """Invoked at the end of each test to record the outcome."""
        _LOGGER.debug("pytest_runtest_makereport")
        outcome = yield
        report = outcome.get_result()
        if report.when != "call":
            return
        report.task_result_args = (
            item.session.stash[SCRAPE_RECORD_STASH_KEY],
            TaskResult(
                task_name=extract_task_name(item.nodeid),
                passed=(not report.failed),
                skipped=report.skipped,
                detail=exception_repr(report.longreprtext) if report.failed else "",
            ),
        )

    @pytest.hookimpl(trylast=True)
    def pytest_runtest_logreport(self, report: TestReport) -> None:
        """Invoked at the completion of a test run."""
        _LOGGER.debug("pytest_runtest_logreport: %s %s", report.when, report.outcome)
        if report.when != "call":  # Ignore setup and teardown
            return
        if (task_result_args := getattr(report, "task_result_args", None)) is None:
            raise ValueError(
                "Unable to run eval report with missing 'task_result_args' attribute."
            )
        self._suite.task_result(*task_result_args)

    @pytest.hookimpl(trylast=True)
    def pytest_terminal_summary(self, terminalreporter: Any) -> None:
        """Invoked at the end of the test run to output the test summary."""
        _LOGGER.debug("pytest_terminal_summary")
        for report_file in self._suite.report_paths:
            terminalreporter.write_sep(
                "-",
                f"Generated eval report: {str(report_file)}",
            )
