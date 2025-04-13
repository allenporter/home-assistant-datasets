"""Tests for the eval report generation.

This test will by default not exercise the eval report. This is used for
manual testing only and you need to specity the `--model_output_dir` flag. See
the `conftest.py` methods for setup.

```bash
$ pytest tests/tool/test_eval_report.py  --model_output_dir=/tmp/
$ cat /tmp/report.yaml
```
"""

import io

import pytest

from home_assistant_datasets.tool.data_model import EvalMetric
from home_assistant_datasets.tool.eval_report import (
    create_writer,
    OutputType,
    GOOD_LABEL,
    BAD_LABEL,
)
from .conftest import TestEvalMetric


def test_eval_report(success: bool, eval_metric: EvalMetric) -> None:
    """Test used for exercising the eval report."""
    eval_metric.label = GOOD_LABEL if success else BAD_LABEL
    eval_metric.context = {"test_eval_report": True}
    assert success


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
def test_exception_repr(success: bool, exc: Exception | None) -> None:
    """Test used for exercising the eval report."""
    if not success and exc is not None:
        raise exc


def test_csv_report_writer() -> None:
    """Test a csv report writer."""
    buf = io.StringIO()
    writer = create_writer(OutputType.CSV, cls=TestEvalMetric, fd=buf)
    writer.start()
    writer.row(
        TestEvalMetric(
            uuid="1234",
            task_id="task-id",
            model_id="model_id",
            some_value="val",
            label="Good",
        )
    )
    writer.finish()

    assert (
        buf.getvalue()
        == """task_id,model_id,label,some_value,details
"task-id","model_id","Good","val",""
"""
    )


def test_yaml_report_writer() -> None:
    """Test a yaml report writer."""
    buf = io.StringIO()
    writer = create_writer(OutputType.YAML, cls=TestEvalMetric, fd=buf)
    writer.start()
    writer.row(
        TestEvalMetric(
            uuid="1234",
            task_id="task-id",
            model_id="model_id",
            some_value="val",
            label="Good",
        )
    )
    writer.finish()

    assert (
        buf.getvalue()
        == """---
uuid: '1234'
task_id: task-id
model_id: model_id
label: Good
context: {}
some_value: val

"""
    )


def test_report_writer() -> None:
    """Test a report writer."""
    buf = io.StringIO()
    writer = create_writer(OutputType.REPORT, cls=TestEvalMetric, fd=buf)
    writer.start()
    writer.row(
        TestEvalMetric(
            uuid="1234",
            task_id="task-id-1",
            model_id="model-id",
            some_value="val 1",
            label="Good",
        )
    )
    writer.row(
        TestEvalMetric(
            uuid="4321",
            task_id="task-id-2",
            model_id="model-id",
            some_value="val 2",
            label="Bad",
        )
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
