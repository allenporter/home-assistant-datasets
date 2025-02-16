"""Leaderboard subcommand.

```
usage: home-assistant-datasets leaderboard [-h] {prebuild,build} ...

positional arguments:
  {prebuild,build}  Sub Action

options:
  -h, --help        show this help message and exit
```
"""

from . import prebuild, build, task_report


SUBCMDS = {
    "prebuild": prebuild,
    "build": build,
    "task_report": task_report,
}
__all__ = list(SUBCMDS)
