"""Tests for the eval report generation.

This test will by default not exercise the eval report. This is used for
manual testing only and you need to specity the `--model_output_dir` flag. See
the `conftest.py` methods for setup.
"""

from home_assistant_datasets.tool.data_model import EvalMetric


def test_eval_report(success: bool, eval_metric: EvalMetric) -> None:
    """Test used for exercising the eval report."""
    eval_metric.context = {"test_eval_report": True}
    assert success
