"""Data model used for this evaluation.

This file defines dataclasses that hold data for the eval run, essentially the
output of parsing the yaml files.
"""

import logging
from typing import Any
from dataclasses import dataclass, field
from collections.abc import Generator
import pathlib
from slugify import slugify

from mashumaro.mixins.yaml import DataClassYAMLMixin

# from mashumaro.codecs.yaml import yaml_decode
from mashumaro.config import BaseConfig
import yaml

from home_assistant_datasets.yaml_loaders import yaml_decode

_LOGGER = logging.getLogger(__name__)


@dataclass
class EntityState(DataClassYAMLMixin):
    """An entity state or attributes"""

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
    """Initial entity states to override."""

    expect_changes: dict[str, EntityState] = field(default_factory=dict)
    """The device states to assert on."""

    ignore_changes: dict[str, list[str]] | None = None
    """The device state or attribute changes to ignored."""

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

    output_dir: pathlib.Path
    """The eval task recordwriter output file."""

    synthetic_home_yaml: str
    """The synthetic home content to load."""

    record_id: str
    """Identifier for the synethetic home task."""

    category: str
    """Category used to describe the evaluation task when reporting"""

    input_text: str
    """The conversation input text to state."""

    expect_changes: dict[str, EntityState] | None = None
    """The device states to assert on."""

    ignore_changes: dict[str, list[str]] | None = None
    """The device state changes to ignored."""

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
    record_path: pathlib.Path,
    dataset_path: pathlib.Path,
    output_dir: pathlib.Path,
    categories: set[str],
    count: int | None = None,
) -> Generator[EvalTask, None, None]:
    """Read and validate the dataset."""
    # Generate the record id based on the file path
    relpath = record_path.relative_to(dataset_path)
    assert relpath.name.endswith(".yaml")
    record_id = make_slug(str(relpath)[:-5])

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
                    output_dir=output_dir,
                    synthetic_home_yaml=yaml_contents,
                    record_id=record_id,
                    category=record.category,
                    input_text=sentence,
                    expect_changes=action.expect_changes,
                    ignore_changes=action.ignore_changes,
                )
            else:
                for i in range(0, count):
                    yield EvalTask(
                        output_dir=output_dir,
                        synthetic_home_yaml=yaml_contents,
                        record_id=record_id,
                        category=record.category,
                        input_text=sentence,
                        expect_changes=action.expect_changes,
                        ignore_changes=action.ignore_changes,
                        task_num=i,
                    )


@dataclass
class ModelOutput(DataClassYAMLMixin):
    uuid: str
    task_id: str
    category: str
    task: dict[str, Any]
    response: str
    context: dict[str, Any]
