"""Leaderboard subcommand.

```
usage: home-assistant-datasets leaderboard [-h] {build} ...

positional arguments:
  {build}  Sub Action

options:
  -h, --help        show this help message and exit
```
"""

from . import build, task_report


SUBCMDS = {
    "build": build,
    "task_report": task_report,
}
__all__ = list(SUBCMDS)
