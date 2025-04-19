"""Data collection test fixtures."""

from collections.abc import Generator
import datetime
import pathlib
import logging
from typing import Any
from unittest.mock import patch

import yaml
import pytest
from homeassistant.util import dt as dt_util
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.components.conversation import async_converse

from home_assistant_datasets.datasets.dataset_card import read_dataset_card
from home_assistant_datasets.datasets.assist_eval_task import (
    EvalTask,
)
from home_assistant_datasets.entity_state import EntityStateFixture
from home_assistant_datasets.entity_state.diff import EntityStateDiffFixture
from home_assistant_datasets.scrape import (
    ScrapeConfig,
    write_scrape_context,
    ModelOutputWriter,
)


_LOGGER = logging.getLogger(__name__)

PLUGINS = [
    "home_assistant_datasets.pytest_synthetic_home",
    "home_assistant_datasets.pytest_agent",
    "home_assistant_datasets.tool.fixtures",
    "home_assistant_datasets.pytest_dataset",
    "home_assistant_datasets.pytest_data_loader",
]


def pytest_addoption(parser: Any) -> None:
    """Pytest arguments passed from the `collect` action to the test."""
    parser.addoption("--models")
    parser.addoption("--model_output_dir")


# TODO: Move these into separate fixtures
def pytest_generate_tests(metafunc: Any) -> None:
    """Generate test parameters for the evaluation from flags."""
    # Parameterize tests by the models under development
    models = metafunc.config.getoption("models").split(",")
    metafunc.parametrize("model_id", models, scope="module")

    output_dir = metafunc.config.getoption("model_output_dir")
    pathlib.Path(output_dir).mkdir(exist_ok=True)
    metafunc.parametrize("output_path", [output_dir], scope="module")


@pytest.fixture(name="scrape_config", scope="module")
def scrape_config(model_id: str, dataset: str, output_path: str) -> ScrapeConfig:
    """Fixture to generate a scrape config."""
    dataset_path = pathlib.Path(dataset)
    dataset_card = read_dataset_card(dataset_path)
    return ScrapeConfig(
        dataset=dataset_card.name,
        dataset_path=str(dataset_path),
        dataset_version=dataset_card.version,
        model_id=model_id,
        model_output_path=str(output_path),
    )


@pytest.fixture(name="scrape_record_writer", scope="module", autouse=True)
def scrape_record_writer_fixture(scrape_config: ScrapeConfig) -> None:
    """Fixture to generate a scrape record."""
    write_scrape_context(scrape_config)


@pytest.fixture(name="model_output_writer")
def model_output_writer_fixture(
    scrape_config: ScrapeConfig,
    eval_task: EvalTask,
) -> ModelOutputWriter:
    """Fixture that prepares the eval output writer.

    This output file needs to be unique across the test instances to avoid overwriting. For
    example if you add a parameter based on the system prompt then this needs to create
    a separate file containing an id of the prompt.
    """
    return ModelOutputWriter(scrape_config.eval_task_output_path(eval_task.task_id))


@pytest.fixture(name="context_now", autouse=True)
def context_now_fixture(
    eval_task: EvalTask,
) -> Generator[datetime.datetime | None, None, None]:
    """Fixture to set "now" based on the eval task context."""
    if eval_task.action.context_now is None:
        yield None
        return

    with patch(
        "homeassistant.util.dt.now", return_value=eval_task.action.context_now
    ) as now_dt:
        yield now_dt


@pytest.fixture(name="context_device_id")
def context_device_id_fixture(
    synthetic_home_config_entry: Any,
    device_registry: dr.DeviceRegistry,
    eval_task: EvalTask,
) -> str | None:
    """Fixture to return the Homoe Assistant device id for the current context."""
    if eval_task.action.context_device is None:
        return None
    device_entries = dr.async_entries_for_config_entry(
        device_registry, synthetic_home_config_entry.entry_id
    )
    device_entry_map = {
        identifier[1]: device_entry
        for device_entry in device_entries
        for identifier in device_entry.identifiers
    }
    if context_device_entry := device_entry_map.get(eval_task.action.context_device):
        return context_device_entry.id
    raise ValueError(
        f"Could not find context device '{eval_task.action.context_device}' in synthetic home {synthetic_home_config_entry}: {device_entry_map}"
    )


@pytest.fixture(name="patch_device_id", autouse=True)
def patch_device_id_fixture(context_device_id: str | None) -> Generator[None]:
    """Fixture to insert the LLM context device_id argument to the start of the conversation."""

    if context_device_id is None:
        yield
        return

    original_function = async_converse

    async def add_device_id(*args: Any, **kwargs: Any) -> Any:
        kwargs["device_id"] = context_device_id
        return await original_function(*args, **kwargs)

    with patch(
        "homeassistant.components.conversation.async_converse",
        side_effect=add_device_id,
    ):
        yield


@pytest.fixture(name="entity_state_diff")
def entity_state_diff_fixture(
    hass: HomeAssistant,
    synthetic_home_config_entry: ConfigEntry,
    entity_registry: er.EntityRegistry,
) -> EntityStateDiffFixture:
    """Fixture with a function call to change device state for evaluation."""
    get_state = EntityStateFixture(hass, synthetic_home_config_entry, entity_registry)
    return EntityStateDiffFixture(get_state)


def configure_yaml() -> None:
    """Configure pyyaml with some formatting options specific to our eval records."""

    # Skip any output for unknown tags
    yaml.emitter.Emitter.prepare_tag = lambda self, tag: ""  # type: ignore[method-assign]

    # Make automation dumps look a little nicer in the output reports
    def str_presenter(dumper, data):  # type: ignore[no-untyped-def]
        """configures yaml for dumping multiline strings
        Ref: https://stackoverflow.com/questions/8640959/how-can-i-control-what-scalar-form-pyyaml-uses-for-my-data
        """
        if data.count("\n") > 0:  # check for multiline string
            return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
        return dumper.represent_scalar("tag:yaml.org,2002:str", data)

    yaml.add_representer(str, str_presenter)
    yaml.representer.SafeRepresenter.add_representer(str, str_presenter)


def run_pytest_main(additional_args: list[str], directory: str) -> int:
    """Run pytest with the default set of arguments plus the additional args passed."""

    configure_yaml()

    # nest_asyncio.apply()
    pytest_args = [
        "--no-header",
        "--disable-warnings",
        # Limit to tests in this directory
        directory,
        *additional_args,
    ]
    retcode = pytest.main(
        pytest_args,
        plugins=PLUGINS,
    )
    return retcode
