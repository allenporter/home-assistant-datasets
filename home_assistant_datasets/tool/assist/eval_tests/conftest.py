"""Fixtures for exercising assist solutions."""

import pathlib
from typing import Any

import pytest

from home_assistant_datasets.agent.trace_events import (
    token_stats_from_context,
    find_llm_call,
)
from home_assistant_datasets.metrics import ScrapeRecord
from home_assistant_datasets.tool.data_model import (
    ModelOutput,
    model_output_files,
)


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
    tasks = model_output_files(model_output_path)
    metafunc.parametrize(
        "model_output_file", [pytest.param(str(task)) for task in tasks], scope="module"
    )


@pytest.fixture(autouse=True)
def expected_lingering_tasks() -> bool:
    """Fixtures to avoid tasks around store shutdown."""
    return True


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Fixtures to avoid timers around store shutdown."""
    return True


@pytest.fixture(name="model_output", scope="module")
async def model_output_fixture(model_output_file: str | None) -> ModelOutput | None:
    """Fixture that produces the scaped model output record."""
    if model_output_file is None:
        return None
    model_output_path = pathlib.Path(model_output_file)
    try:
        return ModelOutput.from_yaml(model_output_path.read_text())
    except Exception as err:
        raise ValueError(
            f"Error while reading model output file {model_output_path}: {err}"
        ) from err


@pytest.fixture(name="scrape_record", autouse=True, scope="module")
def scrape_record_fixture(
    pytestconfig: Any,
    model_output: ModelOutput | None,
    model_output_file: str | None,
) -> ScrapeRecord | None:
    """Fixture for the EvalMetric with details about this specific task for reporting."""
    if model_output_file is None or model_output is None:
        return None

    task_prefix = model_output_file.split("-")[0]
    return ScrapeRecord(
        uuid=model_output.uuid,
        task_id=model_output.task_id,
        model_id=model_output.model_id
        or "unknown",  # TODO: Cleanup old records with no model_id
        context=model_output.context,
        token_stats=token_stats_from_context(model_output.context),
        extra_data={
            "category": task_prefix,
            "text": model_output.task["input_text"],
            "tool_call": find_llm_call(
                model_output.context.get("conversation_trace", {})
            ),
            "response": model_output.response,
        },
    )
