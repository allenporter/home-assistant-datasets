"""Tests for the accuracy module."""

import io

from home_assistant_datasets.metrics import TaskResult, ScrapeRecord
from home_assistant_datasets.metrics.accuracy import AccuracySummary


def test_accuracy_summary() -> None:
    """Test AccuracySummary aggregating TaskResults and building a yaml report."""
    buf = io.StringIO()
    writer = AccuracySummary(fd=buf, summary_key="model_id")
    writer.start()
    writer.row(
        ScrapeRecord(
            uuid="1234",
            task_id="task-id-1",
            model_id="model-id",
            extra_data={
                "some_value": "val 1",
            },
        ),
        TaskResult(
            task_name="test",
            passed=True,
        ),
    )
    writer.row(
        ScrapeRecord(
            uuid="1234",
            task_id="task-id-2",
            model_id="model-id",
            extra_data={
                "some_value": "val 2",
            },
        ),
        TaskResult(
            task_name="test",
            passed=False,
        ),
    )
    writer.finish()

    assert (
        buf.getvalue()
        == """---
- model_id: model-id
  good_percent: 50.0%
  confidence_interval: 69.3%
  good: 1
  total: 2

"""
    )
