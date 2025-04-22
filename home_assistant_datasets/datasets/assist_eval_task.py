"""Module for generating individual eval tasks from assist dataset records.

The purpose of this module is to expand a dataset records into the individual
evaluation tasks that need to be performed. A record may have all the
setup for a scenario, then have multiple text phrases which are the
tasks to evaluate thatexercise that scenario.
"""

from dataclasses import dataclass
from collections.abc import Generator
import logging
from slugify import slugify

from mashumaro.mixins.yaml import DataClassYAMLMixin


from .assist_data_loader import Action, Record, RecordSource

__all__ = [
    "EvalTask",
    "generate_assist_eval_tasks",
]

_LOGGER = logging.getLogger(__name__)


@dataclass(kw_only=True, frozen=True)
class EvalTask(DataClassYAMLMixin):
    """Flattened detail about the task that is being evaluated."""

    record_source: RecordSource
    """Identifier for the synthetic home task."""

    category: str | list[str]
    """Category used to describe the evaluation task when reporting"""

    input_text: str
    """The conversation input text to state."""

    action: Action
    """A copy of the action being tested."""

    task_num: int | None = None
    """If running multiple times, the task number under test."""

    @property
    def categories(self) -> list[str]:
        """Labels used for slicing model predictions."""
        if isinstance(self.category, list):
            return self.category
        return [self.category]

    @property
    def task_id(self) -> str:
        """An identifier that labels this area summary evaluation task."""
        assert self.record_source is not None
        # Ignore multi-line problem statements
        text_parts = self.input_text.split("\n")
        id_parts = [
            self.record_source.record_id,
            _make_slug(text_parts[0]),
        ]
        if self.task_num is not None:
            id_parts.append(str(self.task_num))
        return "-".join(id_parts)


def _make_slug(text: str) -> str:
    """Shorthand slugify command"""
    return slugify(text, separator="_")


def generate_assist_eval_tasks(
    record: Record,
    count: int | None = None,
) -> Generator[EvalTask, None, None]:
    """Generate evaluation tasks for the dataset records."""
    assert record.record_source is not None
    for action in record.tests or ():
        if not action.sentences:
            raise ValueError("No sentences defined for the action")
        for sentence in action.sentences:
            for task_num in range(0, count) if count is not None else [None]:
                yield EvalTask(
                    record_source=record.record_source,
                    category=record.category,
                    input_text=sentence,
                    action=action,
                    task_num=task_num,
                )
