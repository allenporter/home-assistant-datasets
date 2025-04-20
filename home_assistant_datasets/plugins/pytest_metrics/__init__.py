"""Module for computing eval metrics from pytest.

This plugin requires that evaluation task tests are annotated with `@pytest.mark.eval_model_outputs`.
The evaluation will run as a pytest test, generate pass or fail reulsts, then
aggregate the results and write them to report files.

The lifecycle of tests and plugin are:
- The metrics plugin expects `--model_output_dir` to point to an output directory.
- All tests are examined for presence of `@pytest.mark.eval_model_outputs` which determines
  the set of tasks to evaluate.
- The plugin setup will look at all scrape files in the output directory.
- The evaluation tasks (tests) are parameterized with each relevant scrape file.
- The plugin examines a test rules with a success, failure, or skip if not relevant.
- The plugin report suite will write aggregated metrics to a report file.
- The plugin report suite will write detailed metrics to a report file.

Internally, the model outputs are read as a `ScrapeRecord` dataclass. This identifies
the record written by a previous model scrape.

Each pytest test is an eval task. This plugin will examine the pytest output
and create a `TaskResult` that indicates pass or failure.
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
from home_assistant_datasets.scrape import ModelOutput
from home_assistant_datasets.metrics.report_suite import (
    ReportSuite,
    ReportSuiteConfig,
    exception_repr,
    extract_task_name,
)
from home_assistant_datasets.metrics.scrape_reader import (
    model_output_files,
    read_model_output,
    scrape_record_from_output,
)

__all__ = []

_LOGGER = logging.getLogger(__name__)

SUITE_STASH_KEY = pytest.StashKey[ReportSuite]()
SCRAPE_RECORD_STASH_KEY = pytest.StashKey[ScrapeRecord]()


def pytest_addoption(parser: pytest.Parser) -> None:
    """Pytest arguments passed."""
    parser.addoption(
        "--model_output_dir",
        help="Path to scraped model outputs used for evaluation.",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Fixture to register the ReportSuitePlugin."""
    _LOGGER.debug("pytest_configure")

    config.addinivalue_line(
        "markers",
        "eval_model_outputs(task_prefix=None): This test is used to score any model outputs, limited to an optional task prefix.",
    )

    model_output_dir = config.getoption("model_output_dir")
    if not model_output_dir:
        return
    suite = ReportSuite(
        ReportSuiteConfig(output_dir=pathlib.Path(model_output_dir)),
    )
    plugin = ReportSuitePlugin(suite)
    config.pluginmanager.register(plugin)

    config.stash[SUITE_STASH_KEY] = suite


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Generate test parameters for a test.

    Assist tests are parameterized by each model output.
    """
    markers = list(metafunc.definition.iter_markers(name="eval_model_outputs"))
    if not markers:
        return
    if not metafunc.config.getoption("model_output_dir"):
        pytest.skip("Test requires --model_output_dir")
    task_id = markers[0].kwargs.get("task_id")

    model_output_dir = metafunc.config.getoption("model_output_dir")
    model_output_path = pathlib.Path(model_output_dir)
    model_outout_files = model_output_files(
        model_output_path,
        task_id=task_id,
    )
    metafunc.parametrize(
        "model_output_file",
        [pytest.param(str(task)) for task in model_outout_files],
        ids=[str(task.relative_to(model_output_path)) for task in model_outout_files],
    )


@pytest.fixture(name="model_output", autouse=True)
def model_output_fixture(model_output_file: str) -> ModelOutput:
    """Fixture to read the ScrapeRecord from a ModelOutput file."""
    return read_model_output(pathlib.Path(model_output_file))


@pytest.fixture(name="scrape_record", autouse=True)
def scrape_record_fixture(model_output: ModelOutput) -> ScrapeRecord:
    """Fixture to read the ScrapeRecord from a ModelOutput file."""
    return scrape_record_from_output(model_output)


@pytest.fixture(name="consume_scrape_record", autouse=True)
def consume_scrape_record_fixture(
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
