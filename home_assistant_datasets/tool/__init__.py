"""Home Assistant Datasets command line tools.

```
usage: home-assistant-datasets [-h] [--debug] {leaderboard,convert,benchmark} ...

Home Assistant Datasets Utility

positional arguments:
  {leaderboard,convert,benchmark}
                        Action

options:
  -h, --help            show this help message and exit
  --debug               Enable log output
```
"""

__all__ = [
    "leaderboard",
    "convert",
    "benchmark",
]
