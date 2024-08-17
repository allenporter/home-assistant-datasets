"""Tests for llama3 prompt building."""

from syrupy import SnapshotAssertion
import pathlib

from home_assistant_datasets.prompt import llama3


TOOLS = [
    llama3.Tool(
        name="get_current_conditions",
        description="Get the current weather conditions for a specific location",
        parameters={"location": {"type": "string"}},
    )
]
TOOL_CALLS = [
    llama3.ToolCall(
        name="get_current_conditions",
        arguments={"location": "San Francisco, CA"},
    )
]


def test_empty_messages(snapshot: SnapshotAssertion) -> None:
    """Test an empty list of messages."""

    assert llama3.build_prompt(messages=[]) == snapshot


def test_system(snapshot: SnapshotAssertion) -> None:
    """Test a single system message."""

    prompt = llama3.build_prompt(
        messages=[llama3.Message(role="system", content="You are a helpful assistant.")]
    )
    assert prompt == snapshot


def test_conversation(snapshot: SnapshotAssertion) -> None:
    """Test a conversation."""

    prompt = llama3.build_prompt(
        messages=[
            llama3.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            llama3.Message(role="user", content="What is the capital of France?"),
            llama3.Message(role="assistant", content="The capital of France is Paris."),
        ]
    )
    assert prompt == snapshot


def test_system_tools(snapshot: SnapshotAssertion) -> None:
    """Test a system message with tools."""

    prompt = llama3.build_prompt(
        messages=[
            llama3.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            llama3.Message(
                role="user",
                content="What is the weather like today in SF?",
            ),
        ],
        tools=TOOLS,
    )
    assert prompt == snapshot


def test_tool_call(snapshot: SnapshotAssertion) -> None:
    """Test a tool call with output."""

    prompt = llama3.build_prompt(
        messages=[
            llama3.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            llama3.Message(
                role="user",
                content="What is the weather like today in SF?",
            ),
            llama3.Message(
                role="assistant",
                tool_calls=TOOL_CALLS,
            ),
            llama3.Message(
                role="tool",
                content='{"output": "Clouds giving way to sun Hi: 76° Tonight: Mainly clear early, then areas of low clouds forming Lo: 56°"}',
            ),
        ],
        tools=TOOLS,
    )
    assert prompt == snapshot


def test_tool_call_conversation(snapshot: SnapshotAssertion) -> None:
    """Test a tool call conversation."""

    prompt = llama3.build_prompt(
        messages=[
            llama3.Message(
                role="system",
                content="You are a helpful assistant.",
            ),
            llama3.Message(
                role="user",
                content="What is the weather like today in SF?",
            ),
            llama3.Message(
                role="assistant",
                tool_calls=TOOL_CALLS,
            ),
            llama3.Message(
                role="tool",
                content='{"output": "Clouds giving way to sun Hi: 76° Tonight: Mainly clear early, then areas of low clouds forming Lo: 56°"}',
            ),
            llama3.Message(
                role="assistant",
                content="The weather in SF looks cloudy today.",
            ),
        ],
        tools=TOOLS,
    )
    assert prompt == snapshot


def test_converation_record(snapshot: SnapshotAssertion) -> None:
    """Test a training record."""

    message = llama3.ConversationRecord.from_dict(
        {
            "instructions": "You are a helpful assistant.",
            "tools": [tool.to_dict() for tool in TOOLS],
            "input": "What is the weather like today in SF?",
            "output": "I will call a weather tool",
            "tool_calls": [call.to_dict() for call in TOOL_CALLS],
        }
    )
    prompt = llama3.build_prompt_record(message)
    assert prompt == snapshot


def test_converation_record_output(snapshot: SnapshotAssertion) -> None:
    """Test a training record."""

    message = llama3.ConversationRecord.from_dict(
        {
            "instructions": "You are a helpful assistant.",
            "tools": [tool.to_dict() for tool in TOOLS],
            "input": "What is the weather like today in SF?",
            "output": "I can't help you with that.",
            "tool_calls": None,
        }
    )
    prompt = llama3.build_prompt_record(message)
    assert prompt == snapshot


def test_llama3_dataset_from_conversations(snapshot: SnapshotAssertion) -> None:
    """Test generating a huggingface dataset from conversation records."""

    ds = llama3.llama3_dataset_from_conversations(
        pathlib.Path("datasets/device-actions-v2-collect/train")
    )
    record = next(iter(ds))
    assert "text" in record
    assert record["text"] == snapshot
