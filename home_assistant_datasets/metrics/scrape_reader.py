"""Module for reading scraped model outputs for evaluation."""

import pathlib

from home_assistant_datasets.agent.trace_events import token_stats_from_context, find_llm_call
from home_assistant_datasets.scrape import ModelOutput, SCRAPE_CONTEXT_FILE

from . import ScrapeRecord

__all__ = [
    "model_output_files",
    "read_model_output",
    "scrape_record_from_output",
]


def model_output_files(model_output_dir: pathlib.Path) -> list[pathlib.Path]:
    """Return the list of model output files in the specified path."""
    return [
        report_file
        for model in sorted(list(model_output_dir.glob("*")))
        for report_file in sorted(list(model.glob("*.yaml")))
        if report_file.name != SCRAPE_CONTEXT_FILE
    ]


def read_model_output(model_output_file: pathlib.Path) -> ModelOutput:
    """Read a ModelOutput record from a file."""
    try:
        return ModelOutput.from_yaml(model_output_file.read_text())
    except Exception as err:
        raise ValueError(
            f"Error while reading model output file {model_output_file}: {err}"
        ) from err


def scrape_record_from_output(model_output: ModelOutput) -> ScrapeRecord:
    """Create a ScrapeRecord from a ModelOutput record."""
    return ScrapeRecord(
        uuid=model_output.uuid,
        task_id=model_output.task_id,
        # TODO: Cleanup old records with no model_id
        model_id=model_output.model_id or "unknown",
        # TODO: Is context even used?
        context=model_output.context,
        token_stats=token_stats_from_context(model_output.context),
        extra_data={
            "category": model_output.category,
            "text": model_output.task["input_text"],
            "tool_call": find_llm_call(
                model_output.context.get("conversation_trace", {})
            ),
            "response": model_output.response,
        },
    )
