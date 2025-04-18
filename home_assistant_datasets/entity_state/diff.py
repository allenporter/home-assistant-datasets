"""Module for computing diffs in entity state diffs during an evaluation."""

import enum
from typing import Any, cast

from home_assistant_datasets.entity_state import EntityStateFixture, EntityState

__all__ = [
    "EntityStateDiffFixture",
]


def compare_state(v: Any, other_v: Any) -> bool:
    """Compare values for equivalence."""
    # Coerce some equivalent types for simpler comparisons
    if isinstance(v, tuple) or isinstance(other_v, tuple):
        v = list(v)
        other_v = list(v)
        return cast(bool, v == other_v)

    if isinstance(v, enum.StrEnum) or isinstance(other_v, enum.StrEnum):
        v = str(v)
        other_v = str(other_v)
        return cast(bool, v == other_v)

    if v == other_v:
        return True

    if str(v) == str(other_v):
        return True

    return False


def compute_entity_diff(
    a_state: EntityState, b_state: EntityState, ignored: set[str]
) -> dict[str, Any] | None:
    """Compute a diff between two entity states."""
    a = a_state.as_dict()
    b = b_state.as_dict()

    diff_attributes = set([])
    for k, v in a.items():
        other_v = b.get(k)
        if not compare_state(other_v, v):
            diff_attributes.add(k)
    for k in b:
        if k not in a and k:
            diff_attributes.add(k)
    diff_attributes = set({k for k in diff_attributes if k not in ignored})
    if not diff_attributes:
        return None
    return {
        "expected": {key: a.get(key) for key in diff_attributes},
        "got": {key: b.get(key) for key in diff_attributes},
    }


def get_unexpected_states(
    states: dict[str, EntityState],
    updated_states: dict[str, EntityState],
    expect_changes: dict[str, EntityState],
    ignore_changes: dict[str, list[str]],
) -> dict[str, Any]:
    # Update states to what is expected
    for entity_id, entity_state in (expect_changes or {}).items():
        if entity_id not in states:
            raise ValueError(f"Entity defined in eval task does not exist: {entity_id}")
        if entity_state.state is not None:
            states[entity_id].state = entity_state.state
        if entity_state.attributes is not None:
            if states[entity_id].attributes is None:
                states[entity_id].attributes = {}
            states[entity_id].attributes = {
                **states[entity_id].attributes,  # type: ignore[dict-item]
                **entity_state.attributes,
            }

    for entity_id in updated_states:
        if entity_id not in states:
            raise ValueError(f"Unexpected new entity found: {entity_id}")

    diffs = {}
    for entity_id in states:
        ignored_attributes = (
            set(ignore_changes.get(entity_id, [])) if ignore_changes else set({})
        )
        old = states[entity_id]
        new = updated_states[entity_id]
        if diff := compute_entity_diff(old, new, ignored_attributes):
            diffs[entity_id] = diff
    return diffs


class EntityStateDiffFixture:
    """A fixture related to capturing diffs in entity state during a test."""

    def __init__(self, state_fixture: EntityStateFixture) -> None:
        """Initialize EntityStateDiffFixture."""
        self._state_fixture = state_fixture
        self._setup_states: dict[str, EntityState] | None = None
        self._expect_changes: dict[str, EntityState] | None = None
        self._ignore_changes: dict[str, list[str]] | None = None

    def prepare(
        self,
        expect_changes: dict[str, EntityState],
        ignore_changes: dict[str, list[str]],
    ) -> None:
        """Run at the start of the evaluation to record the current state."""
        self._setup_states = self._state_fixture.get_state()
        self._expect_changes = expect_changes
        self._ignore_changes = ignore_changes

    def get_unexpected_changes(self) -> dict[str, Any] | str:
        """Run at the end of the evaluation to capture unexpected states."""
        if (
            self._setup_states is None
            or self._expect_changes is None
            or self._ignore_changes is None
        ):
            raise ValueError("prepare() function was not called first")

        updated_states = self._state_fixture.get_state()
        try:
            return get_unexpected_states(
                self._setup_states,
                updated_states,
                self._expect_changes,
                self._ignore_changes,
            )
        except ValueError as err:
            return f"Error verifying state: {err}"
