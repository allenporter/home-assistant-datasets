"""Run full pipeline: collect + eval + leaderboard.

```
usage: home-assistant-datasets benchmark all [-h] --model MODEL
                                             [--dataset DATASET | --language {es,fr,de,nl}]
                                             [--synthetic-home-dir DIR]
                                             [--parallel] [--dry-run]
```
"""

import argparse

from ._common import add_common_args
from . import collect, eval, leaderboard

__all__ = []


def create_arguments(parser: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    parser.add_argument(
        "--model", required=True, help="Model ID to evaluate (e.g., devstral-2512)"
    )
    add_common_args(parser)


def run(args: argparse.Namespace) -> int:
    """Run the full pipeline: collect + eval + leaderboard."""
    print("Phase 1/3: Collect")
    print("=" * 60)
    rc_collect = collect.run(args)
    if rc_collect != 0:
        print("\nCollect phase had failures; continuing to eval...\n")

    print("\nPhase 2/3: Eval")
    print("=" * 60)
    rc_eval = eval.run(args)

    print("\nPhase 3/3: Leaderboard")
    print("=" * 60)
    rc_leader = leaderboard.run(args)

    if any(rc != 0 for rc in [rc_collect, rc_eval, rc_leader]):
        print("\nPipeline completed with errors.")
        return 1
    print("\nPipeline completed successfully.")
    return 0
