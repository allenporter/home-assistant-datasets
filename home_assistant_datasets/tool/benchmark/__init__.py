"""Benchmark subcommand.

```
usage: home-assistant-datasets benchmark [-h] {collect,eval,leaderboard,all} ...

positional arguments:
  {collect,eval,leaderboard,all}
                        Sub Action

options:
  -h, --help        show this help message and exit
```
"""

from . import collect, eval, leaderboard, all

SUBCMDS = {
    "collect": collect,
    "eval": eval,
    "leaderboard": leaderboard,
    "all": all,
}
__all__ = list(SUBCMDS)
