"""Fixtures for exercising automation solutions."""

import datetime
from dataclasses import dataclass
from collections.abc import Generator, Callable
import pathlib
from slugify import slugify
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.util import dt as dt_util
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from home_assistant_datasets.tool.data_model import EvalMetric, ModelOutput
from home_assistant_datasets.tool.eval_report import EvalReport, exception_repr
from home_assistant_datasets.blueprint import (
    VALID_BLUEPRINT,
    BlueprintContent,
    BlueprintContentStatus,
    extract_blueprint_content,
)
from home_assistant_datasets.tool.conftest import find_token_stats


FIXTURES = "_fixtures.yaml"
SOLUTION = "solution.yaml"


@dataclass
class AutomationEvalMetric(EvalMetric):
    """EvalMetric with additional information for automation evaluation."""

    details: str | None = None
    """Details about the test failure."""


# pytest context variables used during testing
eval_metric_stash_key = pytest.StashKey[AutomationEvalMetric]()


def pytest_addoption(parser):
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


def pytest_configure(config):
    """Register a plugin that generates the results of the eval."""
    report_dir = config.getoption("report_dir")
    if report_dir is None:
        report_dir = config.getoption("model_output_dir")
    if report_dir is not None:
        report = EvalReport(pathlib.Path(report_dir), AutomationEvalMetric)
        config.pluginmanager.register(report)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: Any, call: Any):
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
            node_parts = report.nodeid.split("::")
            path_parts = node_parts[0].split("/")
            report.eval_metric.task_id = "-".join(
                [path_parts[-2], node_parts[-1].split("[")[0]]
            )
            if report.failed:
                report.eval_metric.details = exception_repr(report.longreprtext)


def pytest_generate_tests(metafunc: Any) -> None:
    """Generate test parameters for the evaluation from flags.

    The model output dir is the directory where prior model predictions
    are stored, which are input for computing evaluation metrics.
    """
    # Parameterize tests by the models under development
    model_output_dir = metafunc.config.getoption("model_output_dir")
    model_id = metafunc.config.getoption("model_id")

    # We're either in the mode of running the groundtruth solution or
    # the predictions from the model output.
    if model_output_dir is None:
        metafunc.parametrize("model_output_file", [None], ids=[SOLUTION])
        metafunc.parametrize("model_id", [None], ids=["solution"])
        return

    # Convert 'light_on_door.test_blueprint' to 'light_on_door'
    task_id_prefix = metafunc.module.__name__.split(".")[0]

    model_output_path = pathlib.Path(model_output_dir)
    models = model_output_path.glob("*")

    # Limit the models to the one under test
    tasks = []
    for model in models:
        if model_id is not None and model_id != model.name:
            continue
        report_files = model.glob(f"{task_id_prefix}*.yaml")
        tasks.extend([str(report_file) for report_file in report_files])

    metafunc.parametrize("model_output_file", [pytest.param(task) for task in tasks])


@pytest.fixture(name="test_path")
def test_path_fixture(request):
    """Fixture to get the dataset name from the currently running test."""
    return pathlib.Path(request.module.__file__).parent


@pytest.fixture
def synthetic_home_yaml(test_path: pathlib.Path) -> str:
    """Fixture to load synthetic home entities."""
    return (test_path / FIXTURES).read_text()


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


# TODO: Move to a common fixture location
@pytest.fixture(name="get_state")
def get_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> Callable[[], dict[str, str]]:
    """Fixture that can state for all synthetic home entities."""

    def func() -> dict[str, str]:
        entity_entries = er.async_entries_for_config_entry(
            entity_registry, synthetic_home_config_entry.entry_id
        )
        return {
            entity_entry.entity_id: hass.states.get(entity_entry.entity_id).state
            for entity_entry in entity_entries
        }

    return func


@pytest.fixture(name="solution_path")
def solution_path_fixture(test_path: pathlib.Path) -> str:
    """Fixture with the name of the blueprint file to load."""
    return str(test_path / SOLUTION)


@pytest.fixture(name="model_output")
async def model_output_fixture(model_output_file: str | None) -> ModelOutput | None:
    """Fixture that produces the scaped model output record."""
    if model_output_file is None:
        return None
    model_output_path = pathlib.Path(model_output_file)
    model_output = ModelOutput.from_yaml(model_output_path.read_text())
    if model_output.model_id is None:
        # Infer the model id from the output path. The model file path historically
        # has been reports/{dataset}/{model_id}/{task_id}.yaml. Going forward the
        # model id will be stored in the model output file to make it more explicit.
        model_output.model_id = model_output_path.parent.name
    return model_output


@pytest.fixture(autouse=True)
def eval_metric(
    pytestconfig: Any,
    model_output: ModelOutput | None,
    model_output_file: str | None,
) -> AutomationEvalMetric | None:
    """Fixture for the EvalMetric with details about this specific task for reporting."""
    if model_output_file is None or model_output is None:
        yield None
        return
    eval_metric = AutomationEvalMetric(
        uuid=model_output.uuid,
        task_id=model_output.task_id,
        model_id=model_output.model_id,
        context={},
        token_stats=find_token_stats(model_output.context.get("conversation_trace", {})),
        duration_ms=model_output.context.get("duration_ms"),
    )
    pytestconfig.stash[eval_metric_stash_key] = eval_metric
    yield pytestconfig.stash[eval_metric_stash_key]
    del pytestconfig.stash[eval_metric_stash_key]


@pytest.fixture(name="model_output_blueprint")
async def blueprint_yaml_fixture(
    model_output: ModelOutput | None,
) -> Generator[BlueprintContent | None]:
    """Fixture to produce the yaml"""
    if model_output is None:
        yield None
        return

    with extract_blueprint_content(model_output.response) as content:
        yield content


@pytest.fixture(name="blueprint_content")
def blueprint_content_fixture(
    solution_path: str, model_output_blueprint: BlueprintContent | None
) -> BlueprintContent:
    """Fixture with the name of the blueprint file to load."""
    if model_output_blueprint is None:
        # We're running against the solution, not a scraped model output
        return BlueprintContent(
            status=VALID_BLUEPRINT,
            filename=solution_path,
            yaml_content=pathlib.Path(solution_path).read_text(),
        )
    return model_output_blueprint


@pytest.fixture(name="automation")
async def automation_fixture(
    hass: HomeAssistant,
    blueprint_content: BlueprintContent,
    automation_config: dict[str, Any],
) -> BlueprintContentStatus:
    """Fixture to set up the blueprint, returns false if the automation seems invalid."""
    if not blueprint_content.status.valid:
        return blueprint_content.status
    assert await async_setup_component(
        hass, "automation", {"automation": [automation_config]}
    )
    await hass.async_block_till_done()

    # Verify the automation is loaded
    slug = slugify(automation_config["alias"], separator="_")
    entity_id = f"automation.{slug}"
    states = hass.states.get(entity_id)
    assert states
    if states.state == "unavailable":
        return BlueprintContentStatus(
            valid=False, error_details="Unable to load automation."
        )
    return VALID_BLUEPRINT
