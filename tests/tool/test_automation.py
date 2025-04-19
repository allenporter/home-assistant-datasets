"""Test for running the automation eval end to end."""

import logging
import pathlib
import subprocess
import tempfile

from syrupy import SnapshotAssertion


_LOGGER = logging.getLogger(__name__)


def run_cmd(cmds: list[str]) -> None:
    """Run the specified commands."""
    _LOGGER.debug(cmds)
    p = subprocess.Popen(cmds, stdout=subprocess.PIPE)
    (cmd_output, _) = p.communicate()
    _LOGGER.debug("Output: %s", cmd_output)
    return p.returncode


def test_automation(snapshot: SnapshotAssertion) -> None:
    """Run the automation eval."""
    with tempfile.TemporaryDirectory() as tmpdir:
        run_cmd(
            [
                "home-assistant-datasets",
                "automation",
                "collect",
                "--models=assistant",
                "--dataset=datasets/automations",
                f"--model_output_dir={tmpdir}",
                "--categories=light",
                "--count=1",
            ]
        )
        # Ensure the scrape succeeded before proceeding
        assert (pathlib.Path(tmpdir) / "assistant" / "_scrape_context.yaml").exists()

        run_cmd(
            [
                "home-assistant-datasets",
                "automation",
                "eval",
                "--dataset=datasets/automations",
                f"--model_output_dir={tmpdir}",
            ]
        )

        output_files = sorted(list(pathlib.Path(tmpdir).glob("*.*")))
        assert [output.name for output in output_files] == snapshot
        for output in output_files:
            assert (output.name, output.read_text()) == snapshot
