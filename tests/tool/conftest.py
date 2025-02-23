"""Pytest fixtures for exercising the eval report."""

import pathlib
from typing import Any

import pytest

from home_assistant_datasets.tool.data_model import EvalMetric
from home_assistant_datasets.tool.eval_report import EvalReport

eval_metric_stash_key = pytest.StashKey[EvalMetric]()


def pytest_addoption(parser: Any) -> None:
    """Pytest arguments passed from the `eval` action to the test."""
    parser.addoption("--model_output_dir", default=None)


def pytest_configure(config: Any) -> None:
    """Register a plugin that generates the results of the eval."""
    model_output_dir = config.getoption("model_output_dir")
    if model_output_dir is not None:
        report = EvalReport(pathlib.Path(model_output_dir))
        config.pluginmanager.register(report)


def pytest_generate_tests(metafunc: Any) -> None:
    """Generate test parameters for the evaluation from flags.

    This will add a mode that causes test_eval_report to have a failing test
    case that will make the report more useful.
    """
    model_output_dir = metafunc.config.getoption("--model_output_dir")
    values = [True]
    if model_output_dir is not None:
        values.append(False)
    metafunc.parametrize("success", values)


@pytest.fixture(autouse=True)
def consume_success_fixture(success: Any) -> None:
    """Consume the success value."""
    pass



@pytest.fixture(name="eval_metric")
def eval_metric_fixture(pytestconfig: Any) -> EvalMetric:
    """Add details to the eval reports."""
    eval_metric = EvalMetric(uuid="1234", task_id="task-id",)
    pytestconfig.stash[eval_metric_stash_key] = eval_metric
    yield eval_metric
    del pytestconfig.stash[eval_metric_stash_key]


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: Any, call: Any):
    """Attatch additonal fixture data to the report."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        report.eval_metric = item.config.stash.get(eval_metric_stash_key, None)
