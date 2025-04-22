"""Module for tracking model response accuracy."""

import math
import itertools
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
        good_ratio = self.good / self.total if self.total > 0 else 0
        ci = confidence_interval(good_ratio, self.total)
        return {
            "good_percent": f"{100*good_ratio:0.1f}%",
            "confidence_interval": f"{ci:0.1f}%",
            "good": self.good,
            "total": self.total,
        }


class AccuracySummary(TaskResultWriter):
    """Handles creation of a summarized eval report."""

    def __init__(self, fd: io.TextIOBase | None, summary_key: str | list[str]) -> None:
        """Initialize ReportWriter."""
        self._fd = fd
        self.summary_keys = (
            tuple(summary_key)
            if isinstance(summary_key, list)
            else tuple([summary_key])
        )
        self.accuracy: dict[str, AccuracyTracker] = {}

    def start(self) -> None:
        """Start recording accuracy summary."""
        pass

    def row(self, scrape: ScrapeRecord, result: TaskResult) -> None:
        """Handle a report row collecting the # of good labels for each model."""
        # Build up the iterables that make up the keys. This is primarily to allow
        # multiple categories.
        key_iters = []
        for summary_key in self.summary_keys:
            if (
                key_value := getattr(
                    scrape, summary_key, getattr(result, summary_key, None)
                )
            ) is None:
                report_data = scrape.as_report_data()
                if more_data := result.as_report_data():
                    report_data.update(more_data)

                key_value = report_data.get(summary_key, "unknown")

            if isinstance(key_value, list):
                key_iters.append(key_value)
            else:
                key_iters.append([key_value])

        for parts in itertools.product(*key_iters):
            key = "-".join(parts)
            if key not in self.accuracy:
                self.accuracy[key] = AccuracyTracker()
            self.accuracy[key].row(result)

    def finish(self) -> None:
        """Print the report summary"""
        sorted_keys = sorted(self.accuracy.keys())
        items = []
        summary_key_name = "-".join(self.summary_keys)
        for key in sorted_keys:
            accuracy = self.accuracy[key]
            data = {
                summary_key_name: key,
                **accuracy.finish(),
            }
            items.append(data)
        print(yaml.dump(items, sort_keys=False, explicit_start=True), file=self._fd)
