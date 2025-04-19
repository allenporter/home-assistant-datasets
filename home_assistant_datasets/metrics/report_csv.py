"""Module for generating reports in csv format."""

import io
from typing import Any

from .report import TaskResultWriter, ScrapeRecord, TaskResult

__all__ = [
    "create_csv_writer",
]

# These columns are not useful in CSV reporting
IGNORE_CSV_COLS = {"uuid", "context", "token_stats"}


class CsvWriter(TaskResultWriter):
    """Eval output writer that"""

    def __init__(self, fd: io.TextIOBase | None = None) -> None:
        """Initialize the csv writer."""
        self._cols: list[str] | None = None
        self._fd = fd

    def start(self) -> None:
        """Write the csv header."""

    def row(self, record: ScrapeRecord, result: TaskResult) -> None:
        """Dump the record in csv format."""
        if result.skipped:
            return
        result_data: dict[str, Any] = result.as_report_data()  # type: ignore[assignment]
        item_row = {**record.as_report_data(), **result_data}

        # Print the header
        if self._cols is None:
            self._cols = list(item_row)
            print(",".join(self._cols), file=self._fd)

        vals = []
        for col in self._cols:
            raw_value = item_row[col]
            val = str(raw_value) if raw_value is not None else ""
            # Quote/escape characters
            val = val.replace('"', "'")
            val = val.replace("\n", "\\n")
            vals.append(f'"{val}"')
        print(",".join(vals), file=self._fd)

    def finish(self) -> None:
        """Finish writing the csv file."""
        pass


def create_csv_writer(fd: io.TextIOBase | None = None) -> TaskResultWriter:
    """Create a writer for the output type."""
    return CsvWriter(fd)
