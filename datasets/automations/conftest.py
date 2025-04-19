"""Fixtures for exercising automation solutions."""

from collections.abc import Generator, Callable
import pathlib
from slugify import slugify
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from home_assistant_datasets.agent.trace_events import token_stats_from_context
from home_assistant_datasets.entity_state import EntityStateFixture
from home_assistant_datasets.metrics import ScrapeRecord
from home_assistant_datasets.blueprint import (
    VALID_BLUEPRINT,
    BlueprintContent,
    BlueprintContentStatus,
    extract_blueprint_content,
)
from home_assistant_datasets.scrape import ModelOutput

FIXTURES = "_fixtures.yaml"
SOLUTION = "solution.yaml"


pytest_plugins = [
    "home_assistant_datasets.plugins.pytest_synthetic_home",
]

# Required to run benchmarks against solutions.
#
# def pytest_addoption(parser):
#     """Pytest arguments passed from the `eval` action to the test."""
#     parser.addoption(
#         "--model_output_dir",
#         action="store",
#         default=None,
#         help="Specifies the model output directory from `collect`.",
#     )


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
        metafunc.parametrize(
            "model_output_file", [None], ids=[SOLUTION], scope="module"
        )
        return

    # Convert 'light_on_door.test_blueprint' to 'light_on_door'
    task_id_prefix = metafunc.module.__name__.split(".")[0]

    model_output_path = pathlib.Path(model_output_dir)
    models = model_output_path.glob("*")

    # Limit the models to the one under test
    tasks = []
    for model in models:
        report_files = model.glob(f"{task_id_prefix}*.yaml")
        tasks.extend([str(report_file) for report_file in report_files])

    metafunc.parametrize(
        "model_output_file", [pytest.param(task) for task in tasks], scope="module"
    )


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


@pytest.fixture(name="get_state")
def get_state_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> Callable[[], dict[str, str]]:
    """Fixture that can state for all synthetic home entities."""

    entity_state = EntityStateFixture(
        hass, synthetic_home_config_entry, entity_registry
    )

    def func() -> dict[str, str]:
        return {
            entity_id: state.state
            for entity_id, state in entity_state.get_state().items()
        }

    return func


@pytest.fixture(name="solution_path")
def solution_path_fixture(test_path: pathlib.Path) -> str:
    """Fixture with the name of the blueprint file to load."""
    return str(test_path / SOLUTION)


@pytest.fixture(name="model_output", scope="module")
def model_output_fixture(model_output_file: str | None) -> ModelOutput | None:
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


@pytest.fixture(name="scrape_record", autouse=True, scope="module")
def scrape_record_fixture(model_output: ModelOutput | None) -> ScrapeRecord | None:
    """Fixture for the ScrapeRecord with details about this specific task for reporting."""
    if model_output is None:
        return None
        return
    return ScrapeRecord(
        uuid=model_output.uuid,
        task_id=model_output.task_id,
        model_id=model_output.model_id,
        token_stats=token_stats_from_context(model_output.context),
    )


@pytest.fixture(name="model_output_blueprint")
def blueprint_yaml_fixture(
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
