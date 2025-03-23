"""Fixtures for exercising assist solutions."""

import datetime
from dataclasses import dataclass
from collections.abc import Generator
import pathlib
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from home_assistant_datasets.tool.data_model import EvalMetric, ModelOutput
from home_assistant_datasets.tool.eval_report import (
    EvalReport,
    exception_repr,
)
from home_assistant_datasets.tool.fixtures.conftest import (
    find_token_stats,
    find_llm_call,
)


@dataclass(kw_only=True)
class AssistEvalMetric(EvalMetric):
    """Eval Metric for the assist dataset."""

    category: str
    task_prefix: str
    text: str
    response: str
    tool_call: dict[str, Any] | None
    details: str | None = None


# pytest context variables used during testing
eval_metric_stash_key = pytest.StashKey[AssistEvalMetric]()


def pytest_addoption(parser) -> None:  # type: ignore[no-untyped-def]
    """Pytest arguments passed from the `eval` action to the test."""
    parser.addoption(
        "--model_output_dir",
        action="store",
        default=None,
        help="Specifies the model output directory from `collect`.",
    )
    parser.addoption(
        "--report_dir",
        action="store",
        default=None,
        help="Specifies the directory where the report will be written, or defaults to --model_output_dir.",
    )
    parser.addoption(
        "--model_id",
        action="store",
        default=None,
        help="Specifies the model under test.",
    )


def pytest_configure(config) -> None:  # type: ignore[no-untyped-def]
    """Register a plugin that generates the results of the eval."""
    report_dir = config.getoption("report_dir")
    if report_dir is None:
        report_dir = config.getoption("model_output_dir")
    if report_dir is not None:
        report = EvalReport(pathlib.Path(report_dir), AssistEvalMetric)
        config.pluginmanager.register(report)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: Any, call: Any) -> Generator[None, Any, None]:
    """Attach additional fixture data to the report."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        report.eval_metric = item.config.stash.get(eval_metric_stash_key, None)
        if report.eval_metric is not None:
            # We can use the path and test name as the task id since it is more
            # descriptive than the original problem name used as a task.
            # For a nodeid like:
            #  datasets/automations/light_on_door/test_blueprint.py::test_light_timeout[..../]
            # We want a task id of `light_on_door-test_light_timeout`
            if report.eval_metric.task_id is None:
                node_parts = report.nodeid.split("::")
                path_parts = node_parts[0].split("/")
                report.eval_metric.task_id = "-".join(
                    [path_parts[-2], node_parts[-1].split("[")[0]]
                )
            if report.failed:
                report.eval_metric.details = exception_repr(report.longreprtext)
            else:
                report.eval_metric.details = ""


def pytest_generate_tests(metafunc: Any) -> None:
    """Generate test parameters for the evaluation from flags.

    The model output dir is the directory where prior model predictions
    are stored, which are input for computing evaluation metrics.
    """
    # Parameterize tests by the models under development
    model_output_dir = metafunc.config.getoption("model_output_dir")

    # We're either in the mode of running the groundtruth solution or
    # the predictions from the model output.
    if model_output_dir is None:
        raise ValueError("Required flag --model_output_dir was not specified")

    model_output_path = pathlib.Path(model_output_dir)
    models = model_output_path.glob("*")

    # Limit the models to the one under test
    tasks = []
    for model in models:
        report_files = model.glob("*.yaml")
        tasks.extend([str(report_file) for report_file in report_files])

    metafunc.parametrize("model_output_file", [pytest.param(task) for task in tasks])


@pytest.fixture(autouse=True)
def expected_lingering_tasks() -> bool:
    """Fixtures to avoid tasks around store shutdown."""
    return True


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Fixtures to avoid timers around store shutdown."""
    return True


# TODO: This needs to be really fixed
@pytest.fixture(autouse=True)
def restore_tz(hass: HomeAssistant) -> Generator[None, None, None]:
    """Fix Home Assistant teardown happening too soon."""
    dt_util.set_default_time_zone(datetime.UTC)
    yield
    dt_util.set_default_time_zone(datetime.UTC)


@pytest.fixture(name="model_output")
async def model_output_fixture(model_output_file: str | None) -> ModelOutput | None:
    """Fixture that produces the scaped model output record."""
    if model_output_file is None:
        return None
    model_output_path = pathlib.Path(model_output_file)
    return ModelOutput.from_yaml(model_output_path.read_text())


@pytest.fixture(autouse=True)
def eval_metric(
    pytestconfig: Any,
    model_output: ModelOutput | None,
    model_output_file: str | None,
) -> Generator[AssistEvalMetric | None]:
    """Fixture for the EvalMetric with details about this specific task for reporting."""
    if model_output_file is None or model_output is None:
        yield None
        return

    task_prefix = model_output_file.split("-")[0]

    eval_metric = AssistEvalMetric(
        uuid=model_output.uuid,
        task_id=model_output.task_id,
        # Infer the model id from the output path. The model file path historically
        # has been reports/{dataset}/{model_id}/{task_id}.yaml. Going forward the
        # model id will be stored in the model output file to make it more explicit.
        model_id=model_output.model_id or pathlib.Path(model_output_file).parent.name,
        category=model_output.category,
        task_prefix=task_prefix,
        text=model_output.task["input_text"],
        response=model_output.response,
        tool_call=find_llm_call(model_output.context.get("conversation_trace", {})),
        token_stats=find_token_stats(
            model_output.context.get("conversation_trace", {})
        ),
        duration_ms=model_output.context.get("duration_ms"),
    )
    pytestconfig.stash[eval_metric_stash_key] = eval_metric
    yield pytestconfig.stash[eval_metric_stash_key]
    del pytestconfig.stash[eval_metric_stash_key]
