"""Library for conversations for use with the chat template."""

import json
from dataclasses import dataclass, field, asdict
from typing import Any
from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.mixins.yaml import DataClassYAMLMixin
from mashumaro.config import BaseConfig


@dataclass
class ToolCall(DataClassJSONMixin):
    """A ToolCall dataclass.

    When serializing to a converation record, the arguments are dumped as a string so that the
    conversation can be indexed.  When serializing to a list of tool calls in a message,
    the arguments are preserved as native objects.
    """

    name: str
    arguments: dict[str, Any] = field(
        default=None,
        metadata={"serialize": lambda v: json.dumps(v)},
    )

    def to_message_dict(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize the ToolCall for the prompt."""
        return {
            "type": "function",
            "function": asdict(self)
        }

    class Config(BaseConfig):
        sort_keys = False


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]

    def to_dict(self, **kwargs: Any) -> dict[str, Any]:
        """Serialize the Tool as a dictionary for the prompt."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class Message(DataClassYAMLMixin):
    role: str
    content: str = ""
    tool_calls: list[ToolCall] | None = field(
        default=None,
        metadata={"serialize": lambda v: [c.to_message_dict() for c in v] if v else None},
    )

    class Config(BaseConfig):
        omit_none = True
        sort_keys = False


@dataclass
class ConversationRecord(DataClassYAMLMixin, DataClassJSONMixin):
    instructions: str
    tools: list[Tool] | None = field(
        metadata={"serialize": lambda v: [c.to_dict() for c in v] if v else None},
    )
    input: str
    output: str | None
    tool_calls: list[ToolCall] | None = field(default=None)

    def to_messages(self) -> list[Message]:
        """Generaate a set of messages from the conversation."""
        if not self.output and not self.tool_calls:
            raise ValueError(
                "Could not find assistant output to train, no output or tool_calls"
            )
        return [
            Message(role="system", content=self.instructions),
            Message(role="user", content=self.input or ""),
            Message(
                role="assistant",
                content=self.output or "",
                tool_calls=self.tool_calls,
            ),
        ]

    def to_messages_jsonl(self) -> str:
        """Dump to a messages jsonl record."""
        output = {
            "messages": json.dumps(
                [message.to_dict() for message in self.to_messages()]
            ),
        }
        if self.tools:
            output["tools"] = json.dumps([tool.to_dict() for tool in self.tools])
        return json.dumps(output)

    class Config(BaseConfig):
        omit_none = True
        sort_keys = False
