"""Common librarys for collecting model outputs for evaluation."""

from typing import Any
from slugify import slugify
from dataclasses import dataclass



@dataclass
class SyntheticDeviceState:
    """Information needed to set the synthetic state for an evaluation task."""

    device_name: str
    restorable_attribute: str

    @property
    def state_label(self) -> str:
        """Identifier about the state of the devices under evaluation"""
        return f"{slugify(self.device_name)}-{slugify(self.restorable_attribute)}"


@dataclass
class HomeAssistantContext:
    """Additional context about the actual state of Home Assistant that si being evaluated."""

    device_context: dict[str, Any]
    """Details that reflect the actual synthetic device states under evaluation."""


@dataclass
class ModelConfig:
    """The configuration for the conversation agent under evaluation."""

    conversation_agent_domain: str
    """The domain under evaluation."""

    model_id: str
    """Details about the model name being evaluated if the domain supports multiple models."""



@dataclass
class AreaSummaryTask:
    """Detail about the task that is being evaluated."""

    home_id: str
    """Identifier for the synethetic home."""

    home_name: str
    """Human readable name for the home for context."""

    area_id: str
    """Identifier for the area being summarized."""

    area_name: str
    """Area name within the home that is being summarized and evaluated."""

    device_state: SyntheticDeviceState
    """The device state details  about the state of the devices under evaluation"""

    @property
    def task_id(self) -> str:
        """An identifier that labels this area summary evaluation task."""
        return f"{self.home_id}-{slugify(self.area_name)}-{self.device_state.state_label}"
