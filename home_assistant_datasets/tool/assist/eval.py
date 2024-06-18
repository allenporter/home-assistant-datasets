"""Evaluate data collected from the home assistant conversation agent.

See `assist_collect` for the step to collect data.

You can collect data from the API using the command:
```bash
$ MODEL=gemini-1.5-flash
$ FIXTURES="home-assistant-datasets/datasets/assist/"
$ OUTPUT_DIR="output/$(date +"%Y-%m-%d")/"
$ home-assistant-datasets assist_eval --output_dir=${OUTPUT_DIR}
```

See `assist_eval` for creating offline evaluation reports.

"""

import argparse
import logging


_LOGGER = logging.getLogger(__name__)


def create_arguments(args: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    args.add_argument(
        "--output_dir",
        type=str,
        help="Specifies home assistant API token.",
    )


async def run(args: argparse.Namespace) -> int:

    return 0
