"""Test for running the assist eval end to end command."""

import logging
import pathlib
import subprocess
import sys
import tempfile

from syrupy import SnapshotAssertion


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


def test_assist(snapshot: SnapshotAssertion) -> None:
    """Run the assist eval."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_cmd(
            [
                "home-assistant-datasets",
                "assist",
                "collect",
                "--models=assistant",
                "--dataset=./datasets/assist",
                f"--model_output_dir={tmpdir}",
                "--categories=light",
                "--count=1",
                "--disable-random",
            ]
        )
        # Ensure the scrape succeeded before proceeding
        assert (pathlib.Path(tmpdir) / "assistant" / "_scrape_context.yaml").exists()

        run_cmd(
            [
                "home-assistant-datasets",
                "assist",
                "eval",
                "--dataset=./datasets/assist",
                f"--model_output_dir={tmpdir}",
                "--",
            ]
        )

        output_files = sorted(list(pathlib.Path(tmpdir).glob("*.*")))
        assert [output.name for output in output_files] == snapshot
        for output in output_files:
            assert (output.name, output.read_text()) == snapshot
