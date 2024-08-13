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
            }
        )


@dataclass
class Message:
    role: str
    content: str = ""
    tools: list[Tool] = field(default_factory=list)
    tool_calls: list[ToolCall] = field(default_factory=list)


def build_prompt(messages: list[Message]) -> str:
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
    tools: list[str] | None = next(
        iter(
            [
                tool.json()
                for message in messages
                if message.tools
                for tool in message.tools
            ]
        ),
        None,
    )
    return template.render(
        system=system or "",
        tools=tools,
        messages=messages,
    )
