"""Tests for llama3 prompt building."""

from home_assistant_datasets.prompt import llama3


def test_empty_messages() -> None:
    """Test an empty list of messages."""

    assert llama3.build_prompt(messages=[]) == "<|eot_id|>"


def test_system() -> None:
    """Test an empty list of messages."""

    prompt = llama3.build_prompt(
        messages=[llama3.Message(role="system", content="You are a helpful assistant.")]
    )
    assert (
        prompt
        == """<|start_header_id|>system<|end_header_id|>


You are a helpful assistant.<|eot_id|>"""
    )


def test_system_tools() -> None:
    """Test an empty list of messages."""

    prompt = llama3.build_prompt(
        messages=[
            llama3.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            llama3.Message(
                role="user",
                tools=[llama3.Tool("tool1", parameters={"arg1": {"type": "string"}})],
            ),
        ]
    )
    assert (
        prompt
        == """<|start_header_id|>system<|end_header_id|>


You are a helpful assistant.

You are a helpful assistant with tool calling capabilities. When you receive a tool call response, use the output to format an answer to the orginal use question.<|eot_id|><|start_header_id|>user<|end_header_id|>

Given the following functions, please respond with a JSON for a function call with its proper arguments that best answers the given prompt.

Respond in the format {"name": function name, "parameters": dictionary of argument name and its value}. Do not use variables.

{"name": "tool1", "arguments": {"arg1": {"type": "string"}}}

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    )


def test_tool_call() -> None:
    """Test an empty list of messages."""

    prompt = llama3.build_prompt(
        messages=[
            llama3.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            llama3.Message(
                role="user",
                tools=[
                    llama3.Tool(
                        name="get_current_conditions",
                        description="Get the current weather conditions for a specific location",
                        parameters={"location": {"type": "string"}},
                    )
                ],
            ),
            llama3.Message(
                role="assistant",
                tools=[
                    llama3.ToolCall(
                        name="get_current_conditions",
                        arguments={"location": "San Francisco, CA"},
                    )
                ],
            ),
            llama3.Message(
                role="tool",
                content='{"output": "Clouds giving way to sun Hi: 76° Tonight: Mainly clear early, then areas of low clouds forming Lo: 56°"}',
            ),
        ]
    )
    assert (
        prompt
        == """


"""
    )
