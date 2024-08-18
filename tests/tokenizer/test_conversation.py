"""Tests for the conversation serialization library."""

import dataclasses
from syrupy import SnapshotAssertion
from home_assistant_datasets.tokenizer import conversation

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


def test_message_serialization() -> None:
    """Test message serialization"""
    message = conversation.Message(
        role="user", content="What is the capital of France?"
    )
    assert message.to_dict() == {
        "content": "What is the capital of France?",
        "role": "user",
    }


def test_message_tools_serialization() -> None:
    """Test message serialization"""
    message = conversation.Message(
        role="user",
        content="What is the capital of France?",
        tool_calls=TOOL_CALLS,
    )
    assert message.to_dict() == {
        "content": "What is the capital of France?",
        "role": "user",
        "tool_calls": [
            {
                "type": "function",
                "function": {
                    "arguments": {
                        "location": "San Francisco, CA",
                    },
                    "name": "get_current_conditions",
                },
            },
        ],
    }


def test_conversation_serialization(snapshot: SnapshotAssertion) -> None:
    """Test message serialization"""
    record = conversation.ConversationRecord(
        instructions="You are a helpful assistant",
        input="What is the capital of France?",
        output="Paris.",
        tools=None,
        tool_calls=None,
    )
    assert [message.to_dict() for message in record.to_messages()] == snapshot
    assert record.to_json() == snapshot
    assert record.to_messages_jsonl() == snapshot


def test_conversation_tools_serialization(snapshot: SnapshotAssertion) -> None:
    """Test message serialization"""
    record = conversation.ConversationRecord(
        instructions="You are a helpful assistant.",
        input="What is the weather in San Francisco?",
        output=None,
        tools=TOOLS,
        tool_calls=TOOL_CALLS,
    )
    assert [message.to_dict() for message in record.to_messages()] == snapshot
    assert record.to_json() == snapshot
    assert record.to_messages_jsonl() == snapshot


def test_complex_tool_call_serialization() -> None:
    """Test tool calls."""
    tool_call = conversation.ToolCall(
        name="get_current_conditions",
        arguments={"location": { "type": "city", "name": "San Francisco, CA"} },
    )
    assert tool_call.to_dict() == {
        "name": "get_current_conditions",
        "arguments": '{"location": {"type": "city", "name": "San Francisco, CA"}}',
    }

    tool_call = conversation.ToolCall(
        name="get_current_conditions",
        arguments={"locations": ["San Francisco, CA", "Los Angeles, CA"] },
    )
    assert tool_call.to_dict() == {
        "name": "get_current_conditions",
        "arguments": '{"locations": ["San Francisco, CA", "Los Angeles, CA"]}',
    }
