"""Test for running the automation eval end to end."""

import pathlib
import tempfile

from syrupy import SnapshotAssertion

from . import run_cmd


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
