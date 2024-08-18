"""Tests for chat template builders."""

from syrupy import SnapshotAssertion

from home_assistant_datasets.tokenizer import conversation, chat_template


TOOLS = [
    conversation.Tool(
        name="get_current_conditions",
        description="Get the current weather conditions for a specific location",
        parameters={"location": {"type": "string"}},
    )
]
TOOL_CALLS = [
    conversation.ToolCall(
        name="get_current_conditions",
        arguments={"location": "San Francisco, CA"},
    )
]


def test_system(snapshot: SnapshotAssertion) -> None:
    """Test a single system message."""

    prompt = chat_template.build_prompt(
        messages=[
            conversation.Message(role="system", content="You are a helpful assistant.")
        ],
        add_generation_prompt=True,
    )
    assert prompt == snapshot


def test_conversation(snapshot: SnapshotAssertion) -> None:
    """Test a conversation."""

    prompt = chat_template.build_prompt(
        messages=[
            conversation.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            conversation.Message(role="user", content="What is the capital of France?"),
            conversation.Message(
                role="assistant", content="The capital of France is Paris."
            ),
        ]
    )
    assert prompt == snapshot


def test_system_tools(snapshot: SnapshotAssertion) -> None:
    """Test a system message with tools."""

    prompt = chat_template.build_prompt(
        messages=[
            conversation.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            conversation.Message(
                role="user",
                content="What is the weather like today in SF?",
            ),
        ],
        tools=TOOLS,
        add_generation_prompt=True,
    )
    assert prompt == snapshot


def test_tool_call(snapshot: SnapshotAssertion) -> None:
    """Test a tool call with output."""

    prompt = chat_template.build_prompt(
        messages=[
            conversation.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            conversation.Message(
                role="user",
                content="What is the weather like today in SF?",
            ),
            conversation.Message(
                role="assistant",
                tool_calls=TOOL_CALLS,
            ),
            conversation.Message(
                role="tool",
                content='{"output": "Clouds giving way to sun Hi: 76° Tonight: Mainly clear early, then areas of low clouds forming Lo: 56°"}',
            ),
        ],
        tools=TOOLS,
        add_generation_prompt=True,
    )
    assert prompt == snapshot


def test_tool_call_conversation(snapshot: SnapshotAssertion) -> None:
    """Test a tool call conversation."""

    prompt = chat_template.build_prompt(
        messages=[
            conversation.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            conversation.Message(
                role="user",
                content="What is the weather like today in SF?",
            ),
            conversation.Message(
                role="assistant",
                tool_calls=TOOL_CALLS,
            ),
            conversation.Message(
                role="tool",
                content='{"output": "Clouds giving way to sun Hi: 76° Tonight: Mainly clear early, then areas of low clouds forming Lo: 56°"}',
            ),
            conversation.Message(
                role="assistant",
                content="The weather in SF looks cloudy today.",
            ),
        ],
        tools=TOOLS,
    )
    assert prompt == snapshot


def test_converation_record(snapshot: SnapshotAssertion) -> None:
    """Test a training record."""

    record = conversation.ConversationRecord(
        instructions="You are a helpful assistant.",
        input="What is the weather like today in SF?",
        output="I will call a weather tool",
        tools=TOOLS,
        tool_calls=TOOL_CALLS,
    )
    prompt = chat_template.build_prompt(record.to_messages(), record.tools)
    assert prompt == snapshot


def test_converation_record_output(snapshot: SnapshotAssertion) -> None:
    """Test a training record."""

    record = conversation.ConversationRecord(
        instructions="You are a helpful assistant.",
        input="What is the weather like today in SF?",
        output="I can't help you with that.",
        tools=TOOLS,
    )
    prompt = chat_template.build_prompt(record.to_messages(), record.tools)
    assert prompt == snapshot
