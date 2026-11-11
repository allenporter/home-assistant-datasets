"""Benchmark subcommand.

This is a single entrypoint for running the entire benchmark pipeline for a
model. The other tool subcommands each do one job: `leaderboard` builds the
leaderboard from existing eval reports and `convert` transforms datasets. This
subcommand instead drives the pytest based `collect` and `eval` steps, which are
otherwise run by hand with a long list of pytest arguments, then feeds their
output into the leaderboard build.

The `collect` and `eval` steps run pytest in a subprocess for each dataset,
picking the right test directory and report output directory for the dataset
family (assist or automations) and the installed Home Assistant version.
Use `all` to run `collect`, `eval`, and `leaderboard` in order.

```
usage: home-assistant-datasets benchmark [-h] {collect,eval,leaderboard,all} ...

positional arguments:
  {collect,eval,leaderboard,all}
                        Sub Action

options:
  -h, --help        show this help message and exit
```
"""

from . import all, collect, eval, leaderboard

SUBCMDS = {
    "collect": collect,
    "eval": eval,
    "leaderboard": leaderboard,
    "all": all,
}
__all__ = list(SUBCMDS)
