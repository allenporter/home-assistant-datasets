"""Evaluate the result of the scraped model output."""

import pytest

from home_assistant_datasets.scrape import ModelOutput
from home_assistant_datasets.agent.trace_events import find_llm_call


@pytest.mark.eval_model_outputs
def test_expected_states(model_output: ModelOutput) -> None:
    """Evaluate the states of the scraped model output."""

    # The task is expecting a specific state change to happen
    if model_output.task.get("expect_changes"):
        unexpected_states = model_output.context["unexpected_states"]
        assert not unexpected_states
        assert (
            "Sorry" not in model_output.response
        ), f"Incorrect expected states logic? Response said Sorry but no unexpected states: {model_output.task_id}"
    else:
        unexpected_states = model_output.context.get("unexpected_states")
        assert (
            not unexpected_states
        ), f"Unexpected states but the task is not changing state: {model_output.task_id}"
        pytest.skip()


@pytest.mark.eval_model_outputs
def test_expect_response(model_output: ModelOutput) -> None:
    """Evaluate the expected response of the scraped model output."""

    if not (expect_response := model_output.task.get("expect_response")):
        pytest.skip()

    if isinstance(expect_response, str):
        expect_response = [expect_response]
    assert len(expect_response) > 0, "Expect response should not be empty"
    # Check if the response contains any of the expected words
    text = model_output.response.lower()
    if not any(
        word.lower() in text
        for word in expect_response
    ):
        raise ValueError(f"Response '{model_output.response}' did not contain any of {expect_response}")


@pytest.mark.eval_model_outputs
def test_expect_llm_tool_call_name(model_output: ModelOutput) -> None:
    """Evaluate the expected LLM tool call name of the scraped model output."""
    if not (expect_tool_call := model_output.task.get("expect_tool_call")):
        pytest.skip()

    llm_call = find_llm_call(model_output.context.get("conversation_trace", {}))
    assert llm_call, "Expected LLM call but none found"
    assert expect_tool_call["tool_name"] == llm_call.get("tool_name")


@pytest.mark.eval_model_outputs
def test_expect_llm_tool_call_args(model_output: ModelOutput) -> None:
    """Evaluate the expected LLM tool call args of the scraped model output."""
    if not (expect_tool_call := model_output.task.get("expect_tool_call")):
        pytest.skip()
    if not (tool_args := expect_tool_call.get("tool_args")):
        pytest.skip()

    llm_call = find_llm_call(model_output.context.get("conversation_trace", {}))
    assert llm_call, "Expected LLM call but none found"
    assert tool_args == llm_call.get("tool_args")
