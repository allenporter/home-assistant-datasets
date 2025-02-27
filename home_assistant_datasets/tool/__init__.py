"""Home Assistant Datasets command line tools.

```
usage: home-assistant-datasets [-h] [--debug] {assist,leaderboard,automation} ...

Home Assistant Datasets Utility

positional arguments:
  {assist,leaderboard,automation}
                        Action

options:
  -h, --help            show this help message and exit
  --debug               Enable log output
```
"""

__all__ = [
    "assist",
    "leaderboard",
    "automation",
]
