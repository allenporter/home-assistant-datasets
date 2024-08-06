"""Leaderboard subcommand.

```
usage: home-assistant-datasets leaderboard [-h] {prebuild,build} ...

positional arguments:
  {prebuild,build}  Sub Action

options:
  -h, --help        show this help message and exit
```
"""

from . import prebuild, build


SUBCMDS = {
    "prebuild": prebuild,
    "build": build,
}
__all__ = list(SUBCMDS)
