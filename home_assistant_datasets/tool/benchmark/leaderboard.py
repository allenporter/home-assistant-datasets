"""Build the leaderboard from evaluation reports.

```
usage: home-assistant-datasets benchmark leaderboard [-h] [--dry-run]
```
"""

import argparse

from ._common import REPORTS_DIR

__all__ = []


def create_arguments(parser: argparse.ArgumentParser) -> None:
    """Get parsed passed in arguments."""
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them",
    )


def run(args: argparse.Namespace) -> int:
    """Run the leaderboard build."""
    dry_run = getattr(args, "dry_run", False)
    if dry_run:
        print("[dry-run] leaderboard build")
        return 0

    from home_assistant_datasets.tool.leaderboard import build as leaderboard_build

    # Synthesize the args that leaderboard.build.run() expects
    leaderboard_args = argparse.Namespace(report_dir=str(REPORTS_DIR))
    return leaderboard_build.run(leaderboard_args)
