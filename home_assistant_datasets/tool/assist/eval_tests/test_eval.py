"""Evaluate the result of the scraped model output."""

from home_assistant_datasets.scrape import ModelOutput


def test_evaluate_result(model_output: ModelOutput) -> None:
    """Evaluate the result of the scraped model output compared against the golden."""

    # The task is expecting a specific state change to happen
    if model_output.task.get("expected_states"):
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

    if expect_response := model_output.task.get("expect_response"):
        if isinstance(expect_response, str):
            expect_response = [expect_response]
        assert len(expect_response) > 0, "Expect response should not be empty"
        # Check if the response contains any of the expected words
        text = model_output.response.lower()
        assert any(
            word.lower() in text for word in expect_response
        ), f"Response does not contain expected words '{model_output.response}' did not contain any of {expect_response}"
