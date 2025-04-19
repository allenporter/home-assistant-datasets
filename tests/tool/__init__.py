"""Tests for the command line tool package."""

import logging
import subprocess
import sys

_LOGGER = logging.getLogger(__name__)


def run_cmd(cmds: list[str]) -> None:
    """Run the specified commands."""
    _LOGGER.debug("Running: %s", cmds)
    p = subprocess.Popen(cmds, stdout=subprocess.PIPE)
    (output, _) = p.communicate()
    if p.returncode != 0:
        _LOGGER.info("Command failed: %s", p.returncode)
    if _LOGGER.isEnabledFor(logging.DEBUG):
        print(output.decode(), file=sys.stderr)
    return p.returncode
