"""Evaluate the result of the test."""

from home_assistant_datasets.tool.data_model import ModelOutput


def test_evaluate_result(model_output: ModelOutput) -> None:
    """Evaluate the result of the test."""

    unexpected_states = model_output.context["unexpected_states"]
    assert not unexpected_states
    assert (
        "Sorry" not in model_output.response
    ), f"Incorrect expected states logic? Response said Sorry but no unexpected states: {model_output.task_id}"
