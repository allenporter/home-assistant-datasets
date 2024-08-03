"""Library for managing the eval report output."""

from typing import Any
import enum

import yaml


GOOD_LABEL = "Good"
BAD_LABEL = "Bad"
COLUMNS = [
    "model_id",
    "task_prefix",
    "category",
    "label",
    "text",
    "response",
    "tool_call",
    "entity_diff",
]


class OutputType(enum.StrEnum):
    CSV = "csv"
    YAML = "yaml"
    REPORT = "report"


class WriterBase:
    """Base class for eval output."""

    diff: type[dict] | type[str] = dict

    def start(self) -> None:
        """Write the output start."""

    def row(self, row: dict[str, Any]) -> None:
        """Write an output row."""

    def finish(self) -> None:
        """Write the output summary."""


class YamlWriter(WriterBase):
    """Eval output writer that"""

    def row(self, row: dict[str, Any]) -> None:
        """Dump the record in yaml format."""
        print(yaml.dump(row, sort_keys=False, explicit_start=True))


class CsvWriter(WriterBase):
    """Eval output writer that"""

    diff = str

    def start(self) -> None:
        """Write the csv header."""
        print(",".join(COLUMNS))

    def row(self, row: dict[str, Any]) -> None:
        """Dump the record in csv format."""
        vals = []
        for col in COLUMNS:
            val = str(row[col])
            val = val.replace('"', "'")
            vals.append(f'"{val}"')
        print(",".join(vals))


class ReportWriter(WriterBase):
    """Handles creation of an eval report."""

    def __init__(self) -> None:
        """Initialize ReportWriter."""
        self.model_totals: dict[str, int] = {}
        self.model_good: dict[str, int] = {}

    def row(self, row: dict[str, Any]) -> None:
        """Handle a report row collecting the # of good labels for each model."""
        model_id = row["model_id"]
        if model_id not in self.model_totals:
            self.model_totals[model_id] = 0
            self.model_good[model_id] = 0
        self.model_totals[model_id] += 1
        if row["label"] == GOOD_LABEL:
            self.model_good[model_id] += 1

    def finish(self) -> None:
        """Print the report summary"""
        items = [
            {
                "model_id": model_id,
                "good_percent": f"{100*(self.model_good[model_id] / total):0.1f}%",
                "good": self.model_good[model_id],
                "total": total,
            }
            for model_id, total in self.model_totals.items()
        ]
        print(yaml.dump(items, sort_keys=False, explicit_start=True))


def create_writer(output_type: OutputType) -> WriterBase:
    """Create a writer for the output type."""
    if output_type == OutputType.CSV:
        return CsvWriter()
    if output_type == OutputType.YAML:
        return YamlWriter()
    if output_type == OutputType.REPORT:
        return ReportWriter()
    raise ValueError("Unknown output type: {output_type}")
