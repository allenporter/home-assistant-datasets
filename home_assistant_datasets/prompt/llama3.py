"""Library for creating llama3 prompts."""

from dataclasses import dataclass
from typing import Any
import json
import pathlib
from collections.abc import Generator
from mashumaro.mixins.yaml import DataClassYAMLMixin

from datasets import IterableDataset
from jinja2 import Environment, PackageLoader, select_autoescape

TEMPLATE_FILE = "llama3.j2"


@dataclass
class ToolCall(DataClassYAMLMixin):
    name: str
    arguments: dict[str, Any]

    def json(self) -> str:
        """Serialize the ToolCall as a json string for the prompt."""
        return json.dumps({"name": self.name, "parameters": self.arguments})


@dataclass
class Tool(DataClassYAMLMixin):
    name: str
    description: str
    parameters: dict[str, Any]

    def json(self) -> str:
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
            indent=4,
        )


@dataclass
class Message(DataClassYAMLMixin):
    role: str
    content: str | None = None
    tool_calls: list[ToolCall] | None = None


@dataclass
class ConversationRecord(DataClassYAMLMixin):
    instructions: str
    tools: list[Tool] | None
    input: str
    output: str | None
    tool_calls: list[ToolCall] | None = None


def build_prompt(messages: list[Message], tools: list[Tool] | None = None) -> str:
    """Build a llama3.1 prompt from the list of messages."""

    env = Environment(
        loader=PackageLoader("home_assistant_datasets", "prompt"),
        autoescape=select_autoescape(),
    )
    template = env.get_template(TEMPLATE_FILE)

    system: str | None = next(
        iter([message.content for message in messages if message.role == "system"]),
        None,
    )
    tools_json: str | None = (
        "\n".join([tool.json() for tool in tools]) if tools else None
    )
    return template.render(
        system=system or "",
        tools=tools_json,
        messages=messages,
    )


def build_prompt_record(record: ConversationRecord) -> str:
    """Build a llama3.1 prompt from a training record."""
    if not record.output and not record.tool_calls:
        raise ValueError(
            "Could not find assistant output to train, no output or tool_calls"
        )
    messages: list[Message] = [
        Message(role="system", content=record.instructions),
        Message(role="user", content=record.input),
        Message(role="assistant", content=record.output, tool_calls=record.tool_calls),
    ]
    return build_prompt(messages, record.tools)


def llama3_dataset_from_conversations(dataset_dir: pathlib.Path) -> IterableDataset:
    """Create a huggingface dataset from a training conversation record."""

    def func() -> Generator[dict[str, str], None, None]:
        for filename in dataset_dir.glob("*.yaml"):
            record = ConversationRecord.from_yaml(filename.read_text())
            yield {"text": build_prompt_record(record)}

    return IterableDataset.from_generator(func)
