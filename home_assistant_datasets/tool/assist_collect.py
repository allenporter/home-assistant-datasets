"""Collect data from the assistant tools for a conversation agent.

This will configure the local home assistant enviroment with a conversation
agent a model configuration.

This model configuration supports the assistant pipeline, gpt-4o, or gemini flash:
```yaml
models:
- model_id: assistant
  domain: homeassistant

- model_id: gpt-4o
  domain: openai_conversation
  config_entry_data:
    api_key: sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    chat_model: gpt-4o
  config_entry_options:
    llm_hass_api: assist

- model_id: gemini-1.5-flash
  domain: google_generative_ai_conversation
  config_entry_data:
    api_key: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  config_entry_options:
    chat_model: models/gemini-1.5-flash-latest
    llm_hass_api: assist
```

You can collect data from the API using the command:
```bash
$ MODEL=gemini-1.5-flash
$ FIXTURES="home-assistant-datasets/datasets/assist/"
$ OUTPUT_DIR="output/$(date +"%Y-%m-%d")/"
$ home-assistant-datasets assist_collect --model=${MODEL} --fixtures=${FIXTURES} --output_dir=${OUTPUT_DIR}
```

See `assist_eval` for creating offline evaluation reports.

"""

import argparse
import logging
import slugify
from typing import Any

import aiohttp

from synthetic_home import inventory, common

_LOGGER = logging.getLogger(__name__)



def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--model",
        type=str,
        help="Specifies model to load from the models.yaml file",
    )
    args.add_argument(
        "--fixtures",
        type=str,
        help="Specifies fixtures to load for evaluation",
    )
    args.add_argument(
        "--output_dir",
        type=str,
        help="Specifies home assistant API token.",
    )



async def run(args: argparse.Namespace) -> int:

    return 0
