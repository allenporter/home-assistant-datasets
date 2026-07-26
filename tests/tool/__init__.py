"""Tests for the command line tool package."""

import logging
import os
import pathlib
import subprocess
import sys

_LOGGER = logging.getLogger(__name__)


def run_cmd(cmds: list[str]) -> int:
    """Run the specified commands."""
    if cmds and cmds[0] == "pytest":
        cmds = [sys.executable, "-m", "pytest"] + cmds[1:]
    if _LOGGER.isEnabledFor(logging.DEBUG):
        _LOGGER.debug("Running: %s", " ".join(cmds))
    env = dict(os.environ)
    try:
        import pytest_homeassistant_custom_component

        tc_dir = str(
            pathlib.Path(pytest_homeassistant_custom_component.__file__).parent
            / "testing_config"
        )
        existing_pp = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{tc_dir}:{existing_pp}" if existing_pp else tc_dir
    except ImportError:
        pass
    p = subprocess.Popen(
        cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env
    )
    (output, _) = p.communicate()
    if p.returncode != 0:
        out_str = output.decode() if output else ""
        print(out_str, file=sys.stderr)
        raise RuntimeError(f"Command failed with code {p.returncode}:\n{out_str}")
    return p.returncode
