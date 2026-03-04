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

from home_assistant_datasets.entity_state import EntityStateFixture
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
    "home_assistant_datasets.plugins.pytest_metrics",
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


@pytest.fixture(name="test_path")
def test_path_fixture(request):
    """Fixture to get the dataset name from the currently running test."""
    return pathlib.Path(request.module.__file__).parent


@pytest.fixture
def synthetic_home_yaml(test_path: pathlib.Path) -> str:
    """Fixture to load synthetic home entities."""
    return (test_path / FIXTURES).read_text()


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
