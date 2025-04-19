"""Common classes for reporting."""

from abc import ABC, abstractmethod


from . import ScrapeRecord, TaskResult


__all__ = [
    "ScrapeRecordWriter",
    "TaskResultWriter",
]


class ScrapeRecordWriter(ABC):
    """Base class for eval output."""

    @abstractmethod
    def start(self) -> None:
        """Write the output start."""

    @abstractmethod
    def row(self, scrape: ScrapeRecord) -> None:
        """Write an output row."""

    @abstractmethod
    def finish(self) -> None:
        """Write the output summary."""


class TaskResultWriter(ABC):
    """Base class for eval output."""

    @abstractmethod
    def start(self) -> None:
        """Write the output start."""

    @abstractmethod
    def row(self, scrape: ScrapeRecord, result: TaskResult) -> None:
        """Write an output row."""

    @abstractmethod
    def finish(self) -> None:
        """Write the output summary."""
