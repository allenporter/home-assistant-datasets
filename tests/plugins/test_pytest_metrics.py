"""Tests for the eval report generation pytest plugin."""

from typing import Any
import tempfile

import pytest
import pathlib
from syrupy import SnapshotAssertion

PLUGINS = ["home_assistant_datasets.plugins.pytest_metrics"]
PYTEST_INI = """
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
"""

MODEL_OUTPUT_YAML = """---
uuid: e489d6b0-0f5f-4c49-aced-b9abe1c5104f
task_id: urban_loft_au_light-how_many_lights_are_currently_on_please_respond_with_a_number
model_id: example-model
category: light
task:
  input_text: How many lights are currently on? Please respond with a number.
  expect_changes: {}
  expect_response:
  - 4
response: |-
  Based on the current state of the devices in the home, I can provide you with the number of lights that are currently on.

  4
context:
  unexpected_states: {}
  conversation_trace: {}
  tries: 0
  duration_ms: 3582.574
"""

TEST_FILE_CONTENTS_FORMAT = """
    from dataclasses import dataclass
    from typing import Any

    import pytest

    from home_assistant_datasets.agent.trace_events import TokenStats
    from home_assistant_datasets.metrics.report import ScrapeRecord


    def test_success_1(scrape_record: Any) -> None:
        assert True

    def test_success_2() -> None:
        assert True

    def test_fail() -> None:
        assert False, "Failed test case"

    def test_skip() -> None:
        pytest.skip()

    @pytest.mark.parametrize(
        "exc",
        [
            None,
            ValueError("This is a test"),
            TimeoutError("This is a test"),
            TypeError("This is a test"),
            AssertionError("This is a test"),
        ],
    )
    def test_exception_repr(exc: Exception | None) -> None:
        if exc is not None:
            raise exc
"""


@pytest.fixture(name="tmpdir")
def tmpdir_fixture() -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(tmpdir)


REPORT_OUTPUT_PREFIX = "Generated eval report:"


def parse_report_filenames(tmpdir: str, stdout_list: str) -> list[pathlib.Path]:
    """Parse report filenames from test result stdout.

    Parse the output lines for "Generated eval report" filenames.
    """
    report_files: list[pathlib.Path] = []
    for line in stdout_list:
        if REPORT_OUTPUT_PREFIX not in line or tmpdir not in line:
            continue
        line = line[line.find(tmpdir) :]
        line = line[: line.find(" ")]
        report_files.append(pathlib.Path(line))
    return report_files


def test_verify_report_output_files(
    pytester: Any, tmpdir: str, snapshot: SnapshotAssertion
) -> None:
    """Exercise the report plugin."""

    pytester.makepyfile(TEST_FILE_CONTENTS_FORMAT.format(tmpdir=tmpdir))
    pytester.makeini(PYTEST_INI)

    # Prepare a fake scraped model output file in the model output directory.
    model_output_path = pathlib.Path(tmpdir)
    (model_output_path / "model-1").mkdir()
    (model_output_path / "model-1" / "model-1-output.yaml").write_text(MODEL_OUTPUT_YAML)

    result = pytester.runpytest("--model_output_dir", tmpdir, "-vv", plugins=PLUGINS)

    # Parse the output lines for "Generated eval report" filenames
    report_files = parse_report_filenames(tmpdir, result.stdout.lines)

    # Snapshot the contents of the generated reports
    assert [
        (report_file.name, report_file.read_text()) for report_file in report_files
    ] == snapshot
