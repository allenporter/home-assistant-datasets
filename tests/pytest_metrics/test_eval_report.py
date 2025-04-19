"""Tests for the eval report generation pytest plugin."""

from typing import Any
import tempfile

import pytest
import pathlib
from syrupy import SnapshotAssertion


TEST_FILE_CONTENTS_FORMAT = """
    from dataclasses import dataclass
    from typing import Any

    import pytest

    from home_assistant_datasets.agent.trace_events import TokenStats
    from home_assistant_datasets.metrics.report import ScrapeRecord

    @pytest.fixture(name="scrape_record", autouse=True, scope="module")
    def scrape_record_fixture() -> ScrapeRecord:
        return ScrapeRecord(
            uuid="1234",
            task_id="task-id",
            model_id="model_id",
            token_stats=TokenStats(
                input_tokens=500,
                cached_input_tokens=100,
                output_tokens=250,
                duration_ms=500,
            )
        )

    def test_success_1() -> None:
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
    result = pytester.runpytest(
        "--model_output_dir", tmpdir, plugins=["home_assistant_datasets.pytest_metrics"]
    )

    # Parse the output lines for "Generated eval report" filenames
    report_files = parse_report_filenames(tmpdir, result.stdout.lines)

    # Snapshot the contents of the generated reports
    assert [
        (report_file.name, report_file.read_text()) for report_file in report_files
    ] == snapshot
