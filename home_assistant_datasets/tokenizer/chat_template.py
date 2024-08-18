"""Library for building prompts from the tokenizer chat template."""

import pathlib
from functools import cache
from typing import Any
import json
import logging

from jinja2 import Environment, PackageLoader

from .conversation import Tool, Message

__all__ = [
    "build_prompt",
]

_LOGGER = logging.getLogger(__name__)

TOKENIZER_DIR = pathlib.Path("home_assistant_datasets/tokenizer")
TOKENIZER_CONFIG_JSON = "tokenizer_config.json"

LLAMA3_TOKENIZER = TOKENIZER_DIR / "llama3" / TOKENIZER_CONFIG_JSON


@cache
def load_tokenizer_config(file: pathlib.Path) -> dict[str, Any]:
    """Read the llama3 tokenizer."""
    with file.open() as fd:
        return json.loads(fd.read())  # type: ignore[no-any-return]


# Json function copied from transformers library
def tojson(x, ensure_ascii=False, indent=None, separators=None, sort_keys=False):  # type: ignore
    # We override the built-in tojson filter because Jinja's default filter escapes HTML characters
    # We also expose some options like custom indents and separators
    return json.dumps(
        x,
        ensure_ascii=ensure_ascii,
        indent=indent,
        separators=separators,
        sort_keys=sort_keys,
    )


def raise_exception(args: Any) -> None:
    raise ValueError(args)


def build_prompt(
    messages: list[Message],
    tools: list[Tool] | None = None,
    add_generation_prompt: bool = False,
    tokenizer_config: pathlib.Path | None = None,
) -> str:
    """Build a llama3.1 prompt from the list of messages."""
    config = load_tokenizer_config(tokenizer_config or LLAMA3_TOKENIZER)

    chat_template = config["chat_template"]
    _LOGGER.debug("chat_template: %s", chat_template)

    env = Environment(
        loader=PackageLoader("home_assistant_datasets", "tokenizer"),
    )
    env.filters["tojson"] = tojson
    env.globals["raise_exception"] = raise_exception
    template = env.from_string(chat_template)

    return template.render(
        **config,
        tools=[tool.to_dict() for tool in tools] if tools else None,
        messages=[message.to_dict() for message in messages],
        add_generation_prompt=add_generation_prompt,
        raise_exception=raise_exception,
    )
