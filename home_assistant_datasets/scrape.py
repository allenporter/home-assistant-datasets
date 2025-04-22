"""Libraries related to scraping model outputs and reading scraped outputs.

The scrape config is also used to record the details of how the scrape
was performed when recording model outputs.
"""

from dataclasses import dataclass, field
import datetime
import getpass
from importlib.metadata import version
import logging
import pathlib
import sys
from typing import Any
import uuid


from mashumaro.mixins.yaml import DataClassYAMLMixin
from mashumaro.config import BaseConfig
import yaml

from .yaml_loaders import yaml_decode

__all__ = [
    "ScrapeConfig",
    "ScrapeContext",
    "read_scrape_context",
    "ModelOutput",
    "ModelOutputWriter",
]

_LOGGER = logging.getLogger(__name__)


SCRAPE_CONTEXT_FILE = "_scrape_context.yaml"

# TODO: Combine the scrape config and model output writing so that the entire
# contents of model scrapes are written together. Rename files model output
# and eval task to be specific to scrapes.

@dataclass(kw_only=True)
class ScrapeConfig(DataClassYAMLMixin):
    """Details about a collection of model outputs collected by this tooling."""

    dataset: str
    """The dataset identifier used to generate the predictions."""

    dataset_path: str
    """The path to the dataset used to generate the predictions."""

    dataset_version: str | None = None
    """Additional version information about the dataset."""

    model_id: str
    """The model identifier used to generate the predictions."""

    model_output_path: str
    """Path where model predictions are stored for this scrape."""

    @property
    def scrape_output_path(self) -> pathlib.Path:
        """Base path for output files."""
        return pathlib.Path(self.model_output_path) / self.model_id

    def eval_task_output_path(self, task_id: str) -> pathlib.Path:
        """Return the output filename for an evaluation task run.

        This output file needs to be unique across the test instances to avoid overwriting. For
        example if you add a parameter based on the system prompt then this needs to create
        a separate file containing an id of the prompt.
        """
        return self.scrape_output_path / f"{task_id}.yaml"


@dataclass(kw_only=True)
class ScrapeContext(DataClassYAMLMixin):
    """Details about a collection of model outputs collected by this tooling."""

    uuid: str
    """Unique identifier of the scrape run."""

    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    """The time when the scrape was performed."""

    scrape_config: ScrapeConfig
    """Details about the scrape configuration."""

    version: str
    """The home assistant software version used to create the scrape record."""

    context: dict[str, str] = field(default_factory=dict)
    """Additional context about this scrape record provided by tooling."""

    notes: str = ""
    """Additional manually entered from the developer about this scrape record."""


def read_scrape_context(filename: pathlib.Path) -> ScrapeContext:
    """Read the scrape context from a file."""
    return yaml_decode(filename.open(), ScrapeContext)


def create_scrape_context(scrape_config: ScrapeConfig) -> ScrapeContext:
    """Fixture to generate a scrape record."""
    home_assistant_version = version("homeassistant")
    context: dict[str, Any] = {"user": getpass.getuser() or "unknown"}
    if sys.argv:
        context["argv"] = sys.argv
    return ScrapeContext(
        uuid=str(uuid.uuid4()),
        timestamp=datetime.datetime.now(),
        version=home_assistant_version,
        scrape_config=scrape_config,
        context=context,
        notes="",
    )


def write_scrape_context(scrape_config: ScrapeConfig) -> None:
    """Write scrape context to the configured output path."""
    scrape_context = create_scrape_context(scrape_config)
    scrape_config.scrape_output_path.parent.mkdir(exist_ok=True)
    scrape_config.scrape_output_path.mkdir(exist_ok=True)
    output = scrape_config.scrape_output_path / SCRAPE_CONTEXT_FILE
    output.write_text(yaml.dump(scrape_context, sort_keys=False, explicit_start=True))


@dataclass(kw_only=True)
class ModelOutput(DataClassYAMLMixin):
    """The prediction result of a model."""

    uuid: str
    """A unique id assigned to this prediction."""

    task_id: str
    """An identifier for the task in the dataset."""

    model_id: str | None = None
    """The model identifier used to generate the prediction."""

    category: str | list[str]
    """A label used for slicing model predictions."""

    task: dict[str, Any]
    """Details about the original task for easier inspection of model predictions."""

    response: str
    """The model prediction."""

    context: dict[str, Any]
    """Additional context about the prediction run, e.g. internal model call details."""

    @property
    def categories(self) -> list[str]:
        """Labels used for slicing model predictions."""
        if isinstance(self.category, list):
            return self.category
        return [self.category]

    class Config(BaseConfig):
        omit_none = True
        sort_keys = False


class ModelOutputWriter:
    """Writes records to the eval output."""

    def __init__(self, filename: pathlib.Path):
        """Initialize ModelOutputWriter."""
        self._eval_output = filename

    def write(self, record: ModelOutput) -> None:
        """Write an eval record."""
        self._eval_output.write_text(
            yaml.dump(
                record.to_dict(),
                sort_keys=False,
                explicit_start=True,
                allow_unicode=True,
            )
        )
