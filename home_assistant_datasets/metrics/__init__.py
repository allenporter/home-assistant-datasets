"""Module for computing eval related metrics and reporting."""

from typing import Any
from dataclasses import field, dataclass

from home_assistant_datasets.agent.trace_events import TokenStats


__all__ = [
    "ScrapeRecord",
    "TaskResult",
    "GOOD_LABEL",
    "BAD_LABEL",
    "report",
    "report_suite",
    "accuracy",
    "token_stats",
    "report_csv",
]


GOOD_LABEL = "Good"
BAD_LABEL = "Bad"


@dataclass
class ScrapeRecord:
    """Identifier for a particular model scrape/collection task."""

    uuid: str
    """The unique identifier for the model output/prediction."""

    task_id: str
    """An identifier for the task in the dataset."""

    model_id: str
    """The model identifier used to generate the prediction."""

    context: dict[str, Any] = field(default_factory=dict)
    """Additional context/detail from runtime of evaluating the prediction."""

    token_stats: TokenStats | None = None
    """Token statistics for the model output."""

    extra_data: dict[str, Any] | None = None
    """Additional task specific data to include in the detailed eval report."""

    def as_report_data(self) -> dict[str, Any]:
        """Export the record for reporting."""
        return {
            "task_id": self.task_id,
            "model_id": self.model_id,
            **(self.extra_data if self.extra_data is not None else {}),
        }


@dataclass
class TaskResult:
    """Result of a specific measurement task for a scrape record."""

    task_name: str
    """The name of the particular test for this test e.g. "accuracy"."""

    passed: bool
    """If true, the test passed. If false, it failed."""

    detail: str | None = None
    """Additional detail about the test failure."""

    skipped: bool = False
    """Entirely ignore this pass/fail result.."""

    def as_report_data(self) -> dict[str, Any] | None:
        """Export the record for reporting."""
        if self.skipped:
            return None
        return {
            "task_name": self.task_name,
            "label": GOOD_LABEL if self.passed else BAD_LABEL,
            "details": self.detail,
        }
