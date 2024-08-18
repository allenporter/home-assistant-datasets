"""Library for converations for use with the chat template."""

import pathlib
from functools import cache
from dataclasses import dataclass, field
from typing import Any
import json
import pathlib
import logging
from collections.abc import Generator
from mashumaro.mixins.json import DataClassJSONMixin
from mashumaro.mixins.yaml import DataClassYAMLMixin

from datasets import IterableDataset
from jinja2 import Environment, PackageLoader, TemplateError


@dataclass
class ToolCall(DataClassYAMLMixin):
    name: str
    arguments: dict[str, Any]

    def to_json(self, **kwargs: Any) -> str:
        """Serialize the ToolCall as a json string for the prompt."""
        return json.dumps(
            {"name": self.name, "parameters": self.arguments},
            **{
              **kwargs,
              "sort_keys": False,
            }
         )


@dataclass
class Tool(DataClassYAMLMixin, DataClassJSONMixin):
    name: str
    description: str
    parameters: dict[str, Any]

    def to_json(self, **kwargs: Any) -> str:
        """Serialize the Tool as a json string for the prompt."""
        return json.dumps(
            {
                "type": "function",
                "function": {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.parameters,
                },
            },
            **{
              **kwargs,
              "sort_keys": False,
            }
        )


@dataclass
class Message(DataClassYAMLMixin):
    role: str
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class ConversationRecord(DataClassYAMLMixin, DataClassJSONMixin):
    instructions: str
    tools: list[Tool] | None
    input: str
    output: str | None
    tool_calls: list[ToolCall] | None = None

    def to_messages(self) -> list[Message]:
        """Generaate a set of messages from the conversation."""
        if not self.output and not self.tool_calls:
            raise ValueError(
                "Could not find assistant output to train, no output or tool_calls"
            )
        return [
            Message(role="system", content=self.instructions),
            Message(role="user", content=self.input or ""),
            Message(role="assistant", content=self.output, tool_calls=self.tool_calls or []),
        ]
