"""Common librarys for collecting model outputs for evaluation."""

from typing import Any
from dataclasses import dataclass, field


@dataclass
class HomeAssistantContext:
    """Additional context about the actual state of Home Assistant that is being evaluated."""

    device_context: dict[str, Any] = field(default_factory=dict)
    """Details that reflect the actual synthetic device states under evaluation."""

    conversation_trace: dict[str, Any] = field(default_factory=dict)
    """Details that reflect the actual synthetic device states under evaluation."""


@dataclass
class ModelConfig:
    """The configuration for the conversation agent under evaluation."""

    model_id: str
    """Details about the model name being evaluated if the domain supports multiple models."""

    domain: str
    """The domain under evaluation."""

    config_entry_data: dict[str, Any] | None = None
    """The configuration entry data."""

    config_entry_options: dict[str, Any] | None = None
    """The configuration entry options."""


@dataclass
class Models:
    """The configuration for the full set of models in the config file."""

    models: list[ModelConfig]
    """The list of models under configuration"""
