"""Home Assistant Datasets command line tools.

```
usage: home-assistant-datasets automation [-h] {collect} ...

positional arguments:
  {collect}   Sub Action

options:
  -h, --help  show this help message and exit
```
"""

from . import collect, eval

SUBCMDS = {
    "collect": collect,
    "eval": eval,
}
__all__ = list(SUBCMDS)
