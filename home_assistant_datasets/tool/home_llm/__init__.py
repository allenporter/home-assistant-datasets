"""home-llm subcommand for working with home-llm training datasets.

```
usage: home-assistant-datasets home_llm [-h] {convert} ...

positional arguments:
  {convert}   Sub Action

options:
  -h, --help  show this help message and exit
```
"""

from . import convert

SUBCMDS = {
    "convert": convert,
}
__all__ = list(SUBCMDS)
