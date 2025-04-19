"""Test for running the assist eval end to end command."""

import pathlib
import tempfile

from syrupy import SnapshotAssertion

from . import run_cmd


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
