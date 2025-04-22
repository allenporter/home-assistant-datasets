"""Leaderboard subcommand.

```
usage: home-assistant-datasets convert [-h] {intents} ...

positional arguments:
  {intents}    Sub Action

options:
  -h, --help  show this help message and exit
```
"""

from . import intents


SUBCMDS = {
    "intents": intents,
}
__all__ = list(SUBCMDS)
