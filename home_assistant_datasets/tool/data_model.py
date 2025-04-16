"""Data model used for this evaluation.

This file defines dataclasses that hold data for the eval run, essentially the
output of parsing the yaml files.
"""

from collections.abc import Generator
import dataclasses
from dataclasses import dataclass, field
import datetime
import logging
import pathlib
from slugify import slugify
from typing import Any

from mashumaro.mixins.yaml import DataClassYAMLMixin

from mashumaro.config import BaseConfig
import yaml

from home_assistant_datasets.yaml_loaders import yaml_decode

_LOGGER = logging.getLogger(__name__)

SCRAPE_CONTEXT_FILE = "_scrape_context.yaml"


@dataclass
class EntityState(DataClassYAMLMixin):
    """An entity state or attributes.

    This is used to describe entity state to load, or expected changes.
    """

    state: str | None = None
    attributes: dict[str, Any] | None = None

    def as_dict(self) -> dict[str, Any]:
        """Flattent to a dictionary."""
        data = {}
        if self.state is not None:
            data["state"] = self.state
        if self.attributes:
            data.update(self.attributes)
        return data

    class Config(BaseConfig):
        forbid_extra_keys = True


@dataclass
class Action(DataClassYAMLMixin):
    """An individual data item action."""

    sentences: list[str]
    """Sentences spoken."""

    setup: dict[str, EntityState] = field(default_factory=dict)
    """Initial entity states to override keyed by entity_id."""

    expect_changes: dict[str, EntityState] | None = None
    """The device states to assert on, keyed by entity_id."""

    ignore_changes: dict[str, list[str]] | None = None
    """The device state or attribute changes to ignored, keyed by entity_id."""

    expect_response: str | list[str] | None = None
    """Expect the agent to respond with this substring.

    When specified as a list, the response may match any valid substring in the last.
    """

    context_device: str | None = None
    """Synthetic home device id for the current context of the request."""

    context_now: datetime.datetime | None = None
    """The current time to use during tests."""

    class Config(BaseConfig):
        forbid_extra_keys = False


@dataclass
class Record(DataClassYAMLMixin):
    """Represents an item in the dataset used to configure evaluation."""

    category: str
    """Category used to describe the evaluation task when reporting"""

    tests: list[Action] | None = field(default_factory=list)
    """The set of tasks to evaluate."""


@dataclass
class EvalTask(DataClassYAMLMixin):
    """Flattened detail about the task that is being evaluated."""

    synthetic_home_yaml: str
    """The synthetic home content to load."""

    record_id: str
    """Identifier for the synthetic home task."""

    category: str
    """Category used to describe the evaluation task when reporting"""

    input_text: str
    """The conversation input text to state."""

    context_device: str | None = None
    """The device id for the current context."""

    context_now: datetime.datetime | None = None
    """The current time for the current context."""

    expect_changes: dict[str, EntityState] | None = None
    """The device states to assert on."""

    ignore_changes: dict[str, list[str]] | None = None
    """The device state changes to ignored."""

    expect_response: str | list[str] | None = None
    """Expect the agent to respond with this substring."""

    task_num: int | None = None
    """If running multiple times, the task number under test."""

    @property
    def task_id(self) -> str:
        """An identifier that labels this area summary evaluation task."""
        # Ignore multi-line problem statements
        text_parts = self.input_text.split("\n")
        id_parts = [
            self.record_id,
            make_slug(text_parts[0]),
        ]
        if self.task_num is not None:
            id_parts.append(str(self.task_num))
        return "-".join(id_parts)


def make_slug(text: str) -> str:
    """Shorthand slugify command"""
    return slugify(text, separator="_")


def read_record(filename: pathlib.Path) -> Record:
    """Read the dataset record"""
    return yaml_decode(filename.open(), Record)


def generate_tasks(
    record_id: str,
    record_path: pathlib.Path,
    categories: set[str],
    count: int | None = None,
) -> Generator[EvalTask, None, None]:
    """Read and validate the dataset."""
    # Find the fixtures for this directory. States will be overridden
    # below.
    fixture_path = record_path.parent / "_fixtures.yaml"
    synthetic_home_config = fixture_path.read_text()
    synthetic_home_yaml = yaml.load(synthetic_home_config, Loader=yaml.Loader)

    # Generate the set of eval tasks based on the sentences under test
    record = read_record(record_path)
    if categories and record.category not in categories:
        _LOGGER.debug(
            "Skipping record with category %s (not in %s)", record.category, categories
        )
        return
    for action in record.tests or ():
        if not action.sentences:
            raise ValueError("No sentences defined for the action")

        # Override any state data
        entities = synthetic_home_yaml.get("entities", [])
        entities_dict = {entity["id"]: entity for entity in entities}
        for entity_id, entity_state in (action.setup or {}).items():
            if (found_entity := entities_dict.get(entity_id)) is None:
                raise ValueError(
                    f"Entity `setup` entity id '{entity_id}' found in fixture {fixture_path}"
                )
            if entity_state.state is not None:
                found_entity["state"] = entity_state.state
            if entity_state.attributes is not None:
                found_entity["attributes"] = {
                    **(found_entity.get("attributes", {})),
                    **entity_state.attributes,
                }
            entities_dict[entity_id] = found_entity
        synthetic_home_yaml["entities"] = list(entities_dict.values())
        yaml_contents = yaml.dump(
            synthetic_home_yaml, explicit_start=True, sort_keys=False
        )

        for sentence in action.sentences:
            if count is None:
                yield EvalTask(
                    synthetic_home_yaml=yaml_contents,
                    record_id=record_id,
                    category=record.category,
                    input_text=sentence,
                    context_device=action.context_device,
                    context_now=action.context_now,
                    expect_changes=action.expect_changes,
                    ignore_changes=action.ignore_changes,
                    expect_response=action.expect_response,
                )
            else:
                for i in range(0, count):
                    yield EvalTask(
                        synthetic_home_yaml=yaml_contents,
                        record_id=record_id,
                        category=record.category,
                        input_text=sentence,
                        context_device=action.context_device,
                        context_now=action.context_now,
                        expect_changes=action.expect_changes,
                        ignore_changes=action.ignore_changes,
                        expect_response=action.expect_response,
                        task_num=i,
                    )


@dataclass(kw_only=True)
class ModelOutput(DataClassYAMLMixin):
    """The prediction result of a model."""

    uuid: str
    """A unique id assigned to this prediction."""

    task_id: str
    """An identifier for the task in the dataset."""

    model_id: str | None = None
    """The model identifier used to generate the prediction."""

    category: str
    """A label used for slicing model predictions."""

    task: dict[str, Any]
    """Details about the original task for easier inspection of model predictions."""

    response: str
    """The model prediction."""

    context: dict[str, Any]
    """Additional context about the prediction run, e.g. internal model call details."""


@dataclass(frozen=True, kw_only=True)
class TokenStats:
    """Class for token stats."""

    input_tokens: int | float
    cached_input_tokens: int | float
    output_tokens: int | float

    n_count: int | float = 1
    """Total raw number of requests, which may be more than number of tasks."""


class TokenStatsBank:
    """Class for wriing the summarized eval metric results."""

    def __init__(self) -> None:
        """Initialize report."""
        self.stats: list[TokenStats] = []

    def append(self, stats: TokenStats) -> None:
        """Append a token stats record."""
        self.stats.append(stats)

    def summary_data(self) -> dict[str, Any]:
        """Return a summary of the token stats as a dictionary."""
        return {
            "token_avg": dataclasses.asdict(self.avg()),
            "token_sum": dataclasses.asdict(self.sum()),
            "token_input_cache_ratio": round(
                sum(s.cached_input_tokens for s in self.stats)
                / sum(s.input_tokens for s in self.stats),
                2,
            ),
        }

    def avg(self) -> TokenStats:
        """Average the number of tokens across tasks."""
        return TokenStats(
            input_tokens=round(
                sum(s.input_tokens for s in self.stats) / len(self.stats), 2
            ),
            cached_input_tokens=round(
                sum(s.cached_input_tokens for s in self.stats) / len(self.stats), 2
            ),
            output_tokens=round(
                sum(s.output_tokens for s in self.stats) / len(self.stats), 2
            ),
            n_count=round(sum(s.n_count for s in self.stats) / len(self.stats), 2),
        )

    def sum(self) -> TokenStats:
        """Sum the token stats across tasks."""
        return TokenStats(
            input_tokens=sum(s.input_tokens for s in self.stats),
            cached_input_tokens=sum(s.cached_input_tokens for s in self.stats),
            output_tokens=sum(s.output_tokens for s in self.stats),
            n_count=sum(s.n_count for s in self.stats),
        )


@dataclass
class EvalMetric(DataClassYAMLMixin):
    """Used for pointwise computation based metrics, comparing predictions to groundtruth.

    This currently supports a success or failure rating for a single task.
    Model performance on a dataset can be understood by aggregating ratings
    across all tasks.
    """

    uuid: str
    """The unique identifier for the model output/prediction."""

    task_id: str
    """An identifier for the task in the dataset."""

    model_id: str
    """The model identifier used to generate the prediction."""

    label: str | None = None
    """The groundtruth label for the task, can be 'GOOD' or 'BAD' when computation."""

    context: dict[str, Any] = field(default_factory=dict)
    """Additional context/detail from runtime of evaluating the prediction."""

    token_stats: TokenStats | None = None
    """Token statistics for the model output."""

    duration_ms: float | None = None
    """The duration in milliseconds for the model to generate the prediction."""


@dataclass(kw_only=True)
class ScrapeConfig(DataClassYAMLMixin):
    """Details about a collection of model outputs collected by this tooling."""

    dataset: str
    """The dataset identifier used to generate the predictions."""

    dataset_path: str
    """The path to the dataset used to generate the predictions."""

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


def model_output_files(model_output_path: pathlib.Path) -> list[pathlib.Path]:
    """Return the list of model output files in the specified path."""
    return [
        report_file
        for model in sorted(list(model_output_path.glob("*")))
        for report_file in sorted(list(model.glob("*.yaml")))
        if report_file.name != SCRAPE_CONTEXT_FILE
    ]
