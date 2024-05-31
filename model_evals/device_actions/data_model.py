"""Data model used for this evaluation.

This file defines dataclasses that hold data for the eval run, essentially the
output of parsing the yaml files.
"""

import asyncio
from dataclasses import dataclass
from collections.abc import AsyncGenerator
import pathlib
from slugify import slugify

from synthetic_home import device_types, synthetic_home
from mashumaro import DataClassDictMixin
from mashumaro.codecs.yaml import yaml_decode


DIR = pathlib.Path("model_evals/device_actions/")
HOMES_DIR = DIR / "homes/"
DATASET_DIR = DIR / "dataset/"


def dataset_files() -> list[pathlib.Path]:
    """Read all dataset files"""
    return [
        filename
        for filename in DATASET_DIR.glob("*.yaml")
        if "cover" in str(filename)
    ]


@dataclass
class DeviceState(DataClassDictMixin):
    """Information needed to set the synthetic state for an evaluation task."""

    name: str
    """Device name found in the synthetic home."""

    state: str
    """The state to set on the device."""

    area: str | None = None
    """Device area found in the synthetic home."""

    @property
    def state_label(self) -> str:
        """Identifier about the state of the devices under evaluation"""
        return f"{slugify(self.name)}-{slugify(self.area or ".")}-{slugify(self.state)}"


@dataclass
class Action(DataClassDictMixin):
    """An individual data item action."""

    sentences: list[str]
    """Sentences spoken."""

    device_states: list[DeviceState]
    """The device states to prepare."""

    expected_entity_changes: dict[str, dict[str, str]]
    """The device states to assert on."""

    ignored_entity_changes: dict[str, list[str]] | None = None
    """The device state changes to ignored."""


@dataclass
class Record:
    """Represents an item in the dataset used to configure evaluation."""

    home: str
    """The identifier of the home"""

    actions: list[Action]
    """Actions to perform under evaluation."""


@dataclass
class EvalTask:
    """Flattened detail about the task that is being evaluated."""

    home_id: str
    """Identifier for the synethetic home."""

    input_text: str
    """The conversation input text to state."""

    device_states: list[DeviceState]
    """The device state details to set as the start of the task."""

    expected_entity_changes: dict[str, dict[str, str]]
    """The device states to assert on."""

    ignored_entity_changes: dict[str, list[str]] | None= None
    """The device state changes to ignored."""


    @property
    def task_id(self) -> str:
        """An identifier that labels this area summary evaluation task."""
        return f"{self.home_id}-{[s.state_label for s in self.device_states]}-{self.input_text}"


def read_record(filename: pathlib.Path) -> Record:
    """Read the dataset record"""
    content = filename.read_text()
    return yaml_decode(content, Record)


async def generate_tasks(record: Record) -> AsyncGenerator[EvalTask, None]:
    """Read and validate the dataset."""

    loop = asyncio.get_running_loop()
    home = await loop.run_in_executor(
        None, synthetic_home.load_synthetic_home, HOMES_DIR / f"{record.home}.yaml"
    )
    # Validate the home is formatted properly
    home = home.build()

    registry = device_types.load_device_type_registry()

    for action in record.actions:
        if not action.sentences:
            raise ValueError("No sentences defined for the action")

        # Validate all device states
        for device_state in action.device_states:
            found_device = home.find_devices_by_name(device_state.area, device_state.name)
            if found_device is None:
                raise ValueError(
                    f"Device {device_state.name} not found in synthetic home {record.home} area {device_state.area}"
                )
            if not found_device.device_type:
                raise ValueError(
                    f"Device {device_state.name} does not have a device type"
                )

            found_states = [
                state.name
                for state in registry.device_types[
                    found_device.device_type
                ].device_states
            ]
            if device_state.state not in found_states:
                raise ValueError(
                    f"Device state {device_state.state} does not exist for device type {found_device.device_type}"
                )

        for sentence in action.sentences:
            yield EvalTask(
                home_id=record.home,
                input_text=sentence,
                device_states=action.device_states,
                expected_entity_changes=action.expected_entity_changes,
                ignored_entity_changes=action.ignored_entity_changes,
            )
