"""Module for summarizing token/performance statistics."""

import io

import yaml

from home_assistant_datasets.agent.trace_events import TokenStatsBank

from .report import ScrapeRecord, ScrapeRecordWriter

__all__ = [
    "ModelTokenStats",
]


class ModelTokenStats(ScrapeRecordWriter):
    """Summarize token stats from scrape records for each model."""

    def __init__(self, fd: io.TextIOBase | None = None) -> None:
        """Initialize ReportWriter."""
        self._fd = fd
        self.token_stats: dict[str, TokenStatsBank] = {}

    def start(self) -> None:
        """Start recording model token stats."""
        pass

    def row(self, scrape: ScrapeRecord) -> None:
        """Handle a report row collecting the # of good labels for each model."""
        key = scrape.model_id
        if scrape.token_stats:
            if key not in self.token_stats:
                self.token_stats[key] = TokenStatsBank()
            self.token_stats[key].append(scrape.token_stats)

    def finish(self) -> None:
        """Print the report summary"""
        sorted_keys = sorted(self.token_stats.keys())
        items = []
        for model_id in sorted_keys:
            token_stats = self.token_stats[model_id]
            data = {"model_id": model_id, **token_stats.summary_data()}
            items.append(data)
        print(yaml.dump(items, sort_keys=False, explicit_start=True), file=self._fd)
