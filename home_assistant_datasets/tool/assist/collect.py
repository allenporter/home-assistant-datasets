"""Collect data from the assistant tools for a conversation agent.

This will configure the local home assistant environment with a conversation
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
$ DATASET="home-assistant-datasets/datasets/assist/"
$ OUTPUT_DIR="output/$(date +"%Y-%m-%d")/"
# Run without --dry_run to actually perform the collection (may send LLM RPCs)
$ home-assistant-datasets assist_collect --models=gemini-1.5-flash --dataset=${FIXTURES} --model_output_dir=${OUTPUT_DIR} --dry_run
```

You need to have the synthetic home custom component installed with something like this:

```bash
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/../home-assistant-synthetic-home/"
```

See `assist_eval` for creating offline evaluation reports.

"""

import argparse
import logging

import pytest

_LOGGER = logging.getLogger(__name__)

DEFAULT_DATASET = "datasets/assist"
PLUGINS = [
    "home_assistant_datasets.fixtures",
]


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--dry_run",
        action="store_true",
        help="Only validate the fixtures without actually collecting data.",
    )
    args.add_argument(
        "--models",
        type=str,
        help="Specifies models to load from the models.yaml file",
        required=True,
    )
    args.add_argument(
        "--dataset",
        type=str,
        help="Specifies the test dataset to load for evaluation",
        default=DEFAULT_DATASET,
    )
    args.add_argument(
        "--model_output_dir",
        type=str,
        help="Specifies the directory where output data from the model is stored.",
        required=True,
    )
    args.add_argument(
        "--categories",
        type=str,
        help="Limit evaluation tasks to a specific category",
    )
    args.add_argument(
        "--collect-only",
        action="store_true",
        help="A pytest pass through flag to only collect the list of tests without actually running them.",
    )
    args.add_argument(
        "-s",
        action="store_true",
        help="A pytest pass through flag to show streaming test output.",
    )

    # Flags consistent with pytest for pass through
    args.add_argument(
        "test_path",
        help="A pytest pass through flag optional path for collection actions to perform or full test node.",
        type=str,
        default=None,
        nargs="?",
    )
    verbosity_group = args.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--verbose",
        "-v",
        action="count",
        dest="verbosity",
        help="A pytest pass through flag to increase verbosity.",
    )
    verbosity_group.add_argument(
        "--verbosity",
        action="store",
        type=int,
        metavar="N",
        dest="verbosity",
        help="A pytest pass through flag to set verbosity. Default is 0",
    )
    args.set_defaults(verbosity=0)


def run(args: argparse.Namespace) -> int:
    verbosity = args.verbosity

    # nest_asyncio.apply()
    pytest_args = [
        "--verbosity",
        str(verbosity),
        "--no-header",
        "--disable-warnings",
        # Limit to tests in this directory
        "home_assistant_datasets/tool/assist",
        # See flags defined in conftest.py
        f"--models={args.models or ''}",
        f"--dataset={args.dataset or ''}",
        f"--model_output_dir={args.model_output_dir or ''}",
        f"--categories={args.categories or ''}",
    ]
    if args.test_path:
        pytest_args.append(args.test_path)
    if args.collect_only:
        pytest_args.append("--collect-only")
    if args.s:
        pytest_args.append("-s")
    retcode = pytest.main(
        pytest_args,
        plugins=PLUGINS,
    )
    return retcode
