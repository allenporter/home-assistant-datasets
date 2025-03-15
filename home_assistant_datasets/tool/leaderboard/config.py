"""Configuration for the leaderboard."""

import logging
import pathlib
from dataclasses import dataclass
from collections.abc import Generator

_LOGGER = logging.getLogger(__name__)

REPORT_DIR = "reports"
ASSIST_FAMILY_DATASETS = [
    "assist",
    "assist-mini",
    "assist-mini-stateless",
]
DATASETS = [
    *ASSIST_FAMILY_DATASETS,
    "automations",
]
DATASETS_FOR_AVG = ASSIST_FAMILY_DATASETS

AVERAGE_SCORE = "avg"
SCORED_DATASETS = [
    AVERAGE_SCORE,
    *DATASETS,
]
IGNORE_REPORTS = {
    "reports/assist/2024.6.0dev-baseline-2024-05-27",
    "reports/assist/2024.6.0dev-v1-2024-05-27",
    "reports/assist/2024.6.0dev-v2-2024-05-29",
    "reports/assist/2024.6.0dev-v3-2024-05-31",
}
REPORT_FILE = "reports.yaml"
CSV_FILE = "report.csv"


@dataclass
class EvalReport:
    directory: pathlib.Path
    dataset: str  # e.g. assist-mini
    dataset_label: str  # e.g. home assistant version

    @property
    def report_file(self) -> pathlib.Path:
        return self.directory / REPORT_FILE

    @property
    def csv_file(self) -> pathlib.Path:
        return self.directory / CSV_FILE


def eval_reports(report_dir: pathlib.Path, datasets: list[str]) -> Generator[EvalReport, None, None]:
    """Generate the list of eval reports."""
    for dataset in datasets:
        dataset_dir = report_dir / dataset
        for filename in dataset_dir.iterdir():
            if not filename.is_dir():
                continue
            if str(filename) in IGNORE_REPORTS:
                _LOGGER.debug("Ignoring report directory %s", filename)
                continue

            filename_parts = str(filename).split("/")
            assert filename_parts[0] == REPORT_DIR
            assert len(filename_parts) >= 3, filename_parts
            assert dataset == filename_parts[1], filename_parts
            dataset_label = filename_parts[2]

            yield EvalReport(filename, dataset, dataset_label)
