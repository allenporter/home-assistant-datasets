"""Modules related to assist evaluations that set up or examine entity state."""

from dataclasses import dataclass
from typing import Any

from mashumaro.config import BaseConfig
from mashumaro.mixins.yaml import DataClassYAMLMixin

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.config_entries import ConfigEntry


__all__ = [
    "EntityState",
    "EntityStateFixture",
    "inventory",
    "diff",
]


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


class EntityStateFixture:
    """Helper to bind the needed data for getting entity state."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        entity_registry: er.EntityRegistry,
    ) -> None:
        self._hass = hass
        self._config_entry = config_entry
        self._entity_registry = entity_registry

    def get_state(self) -> dict[str, EntityState]:
        """Return the entity entries."""
        results: dict[str, EntityState] = {}
        for entity_entry in er.async_entries_for_config_entry(
            self._entity_registry, self._config_entry.entry_id
        ):
            state = self._hass.states.get(entity_entry.entity_id)
            assert state
            assert state.state
            results[entity_entry.entity_id] = EntityState(
                state=state.state, attributes=dict(state.attributes or {})
            )
            assert state.state not in (
                "unavailable",
                "unknown",
            ), (
                f"Entity id has unavailable state {entity_entry.entity_id}: {state.state}"
            )

        return results
