"""Command for importing the home-llm dataset.

The home-llm dataset was created before the home assistant assist APIs
were defined around intents. It uses services, so we import the dataset
and convert it to use intents and enhances it with other things like
translations.

First run `generate_home_assistant_data.py` from home-llm to generate a
training dataset, then run this command to convert it.
"""

import argparse
import logging
import pathlib
import subprocess



# from .config import (
#     REPORT_DIR,
#     DATASETS,
#     eval_reports,
# )
# from . import table, chart


__all__ = []

_LOGGER = logging.getLogger(__name__)


DEVICE_NAMES = "data/piles/{language}/pile_of_device_names.csv"
SPECIFIC_ACTIONS = "data/piles/{language}/pile_of_specific_actions.csv"
TEMPLATED_ACTIONS = "data/piles/{language}/pile_of_templated_actions.csv"
TODO_ITEMS = "data/piles/{language}/pile_of_todo_items.txt"
LANGUAGES = ["english"]


GENERATE_CMD_PATH = "{home_llm_dir}/data/generate_home_assistant_data.py"
GENERATE_CMD_ARGS = [
    "--train",
    "--test",
    "--large",
    "--sharegpt",
]


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--home_llm_dir",
        type=str,
        required=True,
        help="Specifies the root of the home-llm git repo.",
    )


def run(args: argparse.Namespace) -> int:
    """Run the command line action."""
    home_llm_dir = pathlib.Path(args.home_llm_dir)
    if not home_llm_dir.is_dir():
        raise ValueError(f"Path --home_llm_dir {home_llm_dir} does not exist.")

    cmds = [
        "python3",
        GENERATE_CMD_PATH.format(home_llm_dir=home_llm_dir),
        *GENERATE_CMD_ARGS,
    ]
    print(cmds)

    p = subprocess.Popen(cmds, stdout=subprocess.PIPE)
    (report_output, _) = p.communicate()
    if p.returncode:
        return p.returncode

    # for language in LANGUAGES:

    #     device_names = home_llm_dir / DEVICE_NAMES.format(language=language)

    #     templated_actions = home_llm_dir / TEMPLATED_ACTIONS.format(language=language)
    #     with templated_actions.open() as fd:
    #         reader = csv.DictReader(fd)
    #         # Ignoring multiplier for now
    #         for line in reader:
    #             phrase = line["phrase"]
    #             print(phrase)
    #             print(line)

    return 0
