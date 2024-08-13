"""Library for creating llama3 prompts."""

from dataclasses import dataclass, field
from typing import Any
import json

from jinja2 import Environment, PackageLoader, select_autoescape

TEMPLATE_FILE = "llama3.j2"


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]

    def json(self) -> str:
        """Serialize the ToolCall as a json string for the prompt."""
        return json.dumps({"name": self.name, "parameters": self.arguments})


@dataclass
class Tool:
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
class Message:
    role: str
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class ConversationRecord:
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
    tools_json: str | None = "\n".join([ tool.json() for tool in tools ]) if tools else None
    return template.render(
        system=system or "",
        tools=tools_json,
        messages=messages,
    )



def build_prompt_record(record: ConversationRecord) -> str:
    """Build a llama3.1 prompt from a training record."""
    if not record.output or not record.tool_calls:
        raise ValueError("Could not find assistant output to train, no output or tool_calls")
    messages: list[Message] = [
        Message(role="system", content=record.instructions),
        Message(role="user", content=input),
        Message(role="assistant", content=record.output, tool_calls=record.tool_calls),
    ]
    return build_prompt(messages, record.tools)
