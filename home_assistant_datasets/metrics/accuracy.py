"""Module for tracking model response accuracy."""

import math
import io
from typing import Any
import yaml

from . import ScrapeRecord, TaskResult
from .report import TaskResultWriter

__all__ = [
    "AccuracyTracker",
    "AccuracySummary",
]


def confidence_interval(p: float, n: int) -> float:
    """Compute the confidence interval for a proportion."""
    if n == 0:
        return 0
    stddev = math.sqrt((p * (1 - p)) / n)
    return 1.96 * stddev * 100


class AccuracyTracker:
    """Tracks accuracy metrics."""

    def __init__(self) -> None:
        """Initialize AccuracyTracker."""
        self.total: int = 0
        self.good: int = 0

    def row(self, item: TaskResult) -> None:
        """Handle a report row collecting the # of good labels for each model."""
        if item.skipped:
            return
        self.total += 1
        if item.passed:
            self.good += 1

    def finish(self) -> dict[str, Any]:
        """Return the report summary"""
        good_ratio = self.good / self.total
        ci = confidence_interval(good_ratio, self.total)
        return {
            "good_percent": f"{100*good_ratio:0.1f}%",
            "confidence_interval": f"{ci:0.1f}%",
            "good": self.good,
            "total": self.total,
        }


class AccuracySummary(TaskResultWriter):
    """Handles creation of a summarized eval report."""

    def __init__(self, fd: io.TextIOBase | None, summary_key: str) -> None:
        """Initialize ReportWriter."""
        self._fd = fd
        self.summary_key = summary_key
        self.accuracy: dict[str, AccuracyTracker] = {}

    def start(self) -> None:
        """Start recording accuracy summary."""
        pass

    def row(self, scrape: ScrapeRecord, result: TaskResult) -> None:
        """Handle a report row collecting the # of good labels for each model."""
        key = getattr(scrape, self.summary_key)
        if key not in self.accuracy:
            self.accuracy[key] = AccuracyTracker()
        self.accuracy[key].row(result)

    def finish(self) -> None:
        """Print the report summary"""
        sorted_keys = sorted(self.accuracy.keys())
        items = []
        for key in sorted_keys:
            accuracy = self.accuracy[key]
            data = {
                self.summary_key: key,
                **accuracy.finish(),
            }
            items.append(data)
        print(yaml.dump(items, sort_keys=False, explicit_start=True), file=self._fd)
