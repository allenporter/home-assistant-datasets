"""Tests for leaderboard build command."""

import argparse
import pathlib

import pytest

from home_assistant_datasets.tool.leaderboard import build


@pytest.fixture
def parser() -> argparse.ArgumentParser:
    """Fixture for argument parser."""
    parser = argparse.ArgumentParser()
    build.create_arguments(parser)
    return parser


def test_create_arguments(parser: argparse.ArgumentParser) -> None:
    """Test argument parsing for leaderboard build."""
    args = parser.parse_args(
        ["--dry-run", "--check", "--output-summary-file", "summary.md"]
    )
    assert args.dry_run is True
    assert args.check is True
    assert args.output_summary_file == "summary.md"
    assert args.report_dir == "reports"


def test_build_check_up_to_date() -> None:
    """Test leaderboard build check against existing repo reports."""
    args = argparse.Namespace(
        report_dir="reports",
        dry_run=False,
        check=True,
        output_summary_file=None,
    )
    assert build.run(args) == 0


def test_build_dry_run_with_summary(tmp_path: pathlib.Path) -> None:
    """Test leaderboard build dry run and summary output."""
    summary_file = tmp_path / "summary.md"
    args = argparse.Namespace(
        report_dir="reports",
        dry_run=True,
        check=False,
        output_summary_file=str(summary_file),
    )
    assert build.run(args) == 0
    assert summary_file.exists()
    summary_content = summary_file.read_text()
    assert "## Home LLM Leaderboard Preview" in summary_content
    assert "| Model |" in summary_content


def test_build_check_out_of_date(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test leaderboard build check returns error when README is out of date."""
    args = argparse.Namespace(
        report_dir="reports",
        dry_run=False,
        check=True,
        output_summary_file=None,
    )
    test_file = pathlib.Path("reports/OUTDATED_README_TEST.md")
    test_file.write_text("outdated content")
    try:
        monkeypatch.setattr(build, "LEADERBOARD_FILE", "OUTDATED_README_TEST.md")
        assert build.run(args) == 1
    finally:
        if test_file.exists():
            test_file.unlink()
