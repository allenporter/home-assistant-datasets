"""Tests the CSV report writer."""

import io

from home_assistant_datasets.metrics import TaskResult, ScrapeRecord
from home_assistant_datasets.metrics.report_csv import create_csv_writer


def test_csv_report_writer() -> None:
    """Test a csv report writer."""
    buf = io.StringIO()
    writer = create_csv_writer(fd=buf)
    writer.start()
    writer.row(
        ScrapeRecord(
            uuid="1234",
            task_id="task-id",
            model_id="model_id",
            extra_data={
                "some_value": "val",
            },
        ),
        TaskResult(
            task_name="test",
            passed=True,
        ),
    )
    writer.finish()

    assert (
        buf.getvalue()
        == """task_id,model_id,some_value,task_name,label,details
"task-id","model_id","val","test","Good",""
"""
    )
