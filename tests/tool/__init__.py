"""Tests for the command line tool package."""

import logging
import os
import subprocess
import sys

_LOGGER = logging.getLogger(__name__)


def run_cmd(cmds: list[str]) -> int:
    """Run the specified commands."""
    if cmds and cmds[0] == "pytest":
        cmds = [sys.executable, "-m", "pytest"] + cmds[1:]
    if _LOGGER.isEnabledFor(logging.DEBUG):
        _LOGGER.debug("Running: %s", " ".join(cmds))
    p = subprocess.Popen(
        cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=os.environ
    )
    (output, _) = p.communicate()
    if p.returncode != 0:
        print(output.decode(), file=sys.stderr)
        _LOGGER.info("Command failed: %s", p.returncode)
    return p.returncode
