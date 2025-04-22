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



def test_categories_list_keys() -> None:
    """Test AccuracySummary with keys that are lists."""
    buf = io.StringIO()
    writer = AccuracySummary(fd=buf, summary_key=["model_id", "category"])
    writer.start()
    writer.row(
        ScrapeRecord(
            uuid="1234",
            task_id="task-id-1",
            model_id="model-id",
            extra_data={
                "category": ["one", "two"],
            }
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
                "category": ["one"],
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
- model_id-category: model-id-one
  good_percent: 50.0%
  confidence_interval: 69.3%
  good: 1
  total: 2
- model_id-category: model-id-two
  good_percent: 100.0%
  confidence_interval: 0.0%
  good: 1
  total: 1

"""
    )
