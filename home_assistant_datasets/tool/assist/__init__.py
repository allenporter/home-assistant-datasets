"""Home Assistant Datasets command line tools.

```
usage: home-assistant-datasets assist [-h] {collect,eval} ...

positional arguments:
  {collect,eval}  Sub Action

options:
  -h, --help      show this help message and exit
```
"""

from . import collect, eval

SUBCMDS = {
    "collect": collect,
    "eval": eval,
}
__all__ = list(SUBCMDS)
