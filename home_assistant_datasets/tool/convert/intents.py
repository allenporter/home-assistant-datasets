"""Convert intents tests into assist llm eval format for intents dataset.

```
usage: home-assistant-datasets convert intents [-h] --intents-repo-dir INTENTS_REPO_DIR
                                               --intents-dataset-dir INTENTS_DATASET_DIR

options:
  -h, --help            show this help message and exit
  --intents-repo-dir INTENTS_REPO_DIR
                        The path to the home-assistant/intents repo which is the source to read from.
  --intents-dataset-dir INTENTS_DATASET_DIR
                        The path to the home-assistant-datasets intents dataset directory to write to.
```
"""

import argparse
import logging
import pathlib
from tqdm import tqdm

from home_assistant_datasets.datasets.convert.intents import convert_intent_tests
from home_assistant_datasets.yaml_loaders import configure_encoders

__all__ = []

_LOGGER = logging.getLogger(__name__)

INTENTS_REPO_TEST_DIR = "tests"


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--intents-repo-dir",
        type=str,
        required=True,
        help="The path to the home-assistant/intents repo which is the source to read from.",
    )
    args.add_argument(
        "--intents-dataset-dir",
        type=str,
        required=True,
        help="The path to the home-assistant-datasets intents dataset directory to write to.",
    )


def run(args: argparse.Namespace) -> int:
    """Run the command line action."""

    intents_repo_dir = pathlib.Path(args.intents_repo_dir) / INTENTS_REPO_TEST_DIR
    if not intents_repo_dir.exists():
        raise ValueError(
            f"Path --intents-repo-dir did not point to repo, file {intents_repo_dir} does not exist"
        )
    intents_dataset_dir = pathlib.Path(args.intents_dataset_dir)

    _LOGGER.debug("Creating destination directory %s", str(intents_dataset_dir))
    intents_dataset_dir.mkdir(exist_ok=True)

    pbar = tqdm()
    configure_encoders()
    convert_intent_tests(intents_repo_dir, intents_dataset_dir, pbar)
    return 0
