"""Module for converting intent test fixtures to assist dataset format."""

import pathlib
import logging
import shutil
from typing import Any

import yaml
from synthetic_home import inventory

from home_assistant_datasets.datasets.assist_data_loader import Record, Action, ToolCall

__all__ = [
    "convert_intent_tests",
]

_LOGGER = logging.getLogger(__name__)

FIXTURES_FILE = "_fixtures.yaml"

# All domains must be explicitly marked as in or out.
SUPPORTED_DOMAINS = {
    "cover",
}
UNSUPPORTED_DOMAINS = {
    "person",
}

# All domains must be explicitly supported or unsupported.
SUPPORTED_INTENTS = {
    "HassTurnOn",
}
UNSUPPORTED_INTENTS = {}


def fixture_filename_parts(filename: pathlib.Path) -> tuple[str, str]:
    """Extract the entity domain and intent under test."""
    parts = filename.stem.rsplit("_", maxsplit=1)
    return (parts[0], parts[1])


def convert_intent_to_tool_call(intent: dict[str, Any]) -> ToolCall:
    """Convert an intent test expected intent to an expected tool call."""
    if not (name := intent.get("name")):
        raise ValueError("Intent call missing 'name' field")
    if not (slots := intent.get("slots")):
        raise ValueError("Intent call missing 'slots' field")
    return ToolCall(tool_name=name, tool_args=slots)


def convert_intent_test(
    intent_test_file: pathlib.Path, intent_dataset_file: pathlib.Path
) -> None:
    """Convert a single intent test file to an intents assist dataset."""
    domain, _ = fixture_filename_parts(intent_test_file)
    content = yaml.load(intent_test_file.open(), Loader=yaml.Loader)
    if not (tests := content.get("tests")):
        raise ValueError(f"Could not find 'tests' in intent test file: {content}")
    actions: list[Action] = []
    for test in tests:
        tool_call = convert_intent_to_tool_call(test["intent"])
        action = Action(
            sentences=test["sentences"],
            expect_response=[test["response"]],
            expect_tool_call=tool_call,
        )
        actions.append(action)
    record = Record(
        category=domain,
        tests=actions,
    )
    intent_dataset_file.write_text(record.to_yaml(omit_none=True))  # type: ignore[arg-type]


def validate_fixture(filename: pathlib.Path) -> None:
    """Validate the fixture path is valid."""
    # Verify the inventory file is valid
    inv = inventory.load_inventory(filename)
    if not (inv.entities or inv.devices or inv.areas):
        raise ValueError(
            f"Fixtures filename {str(filename)} contained no home resources"
        )


def validate_intent_test(filename: pathlib.Path) -> None:
    """Validate the intent test file."""
    yaml.load(filename.open(), Loader=yaml.Loader)


def convert_intent_tests(
    intent_tests_path: pathlib.Path, intents_dataset_path: pathlib.Path
) -> None:
    """Convert a directory of intent tests to an intents assist dataset."""

    if not intent_tests_path.is_dir():
        raise ValueError(f"Intents test path {intent_tests_path} is not a directory")

    intents_dataset_path.mkdir(exist_ok=True)

    dest_dirs: list[pathlib.Path] = []
    fixtures: list[tuple[pathlib.Path, pathlib.Path]] = []
    intent_tests: list[tuple[pathlib.Path, pathlib.Path]] = []

    unknown_domains: set[str] = set()
    unknown_intents: set[str] = set()
    for subdir in intent_tests_path.iterdir():
        if not subdir.is_dir():
            continue
        dest_path = intents_dataset_path / subdir.name
        dest_dirs.append(dest_path)
        for filename in subdir.iterdir():
            dest_filename = dest_path / filename.name
            if filename.name == FIXTURES_FILE:
                fixtures.append((filename, dest_filename))
                continue

            (domain, intent) = fixture_filename_parts(filename)
            if domain in UNSUPPORTED_DOMAINS:
                continue
            if intent in UNSUPPORTED_INTENTS:
                continue
            if domain not in SUPPORTED_DOMAINS:
                unknown_domains.add(domain)
                continue
            if intent not in SUPPORTED_INTENTS:
                unknown_intents.add(intent)

            intent_tests.append((filename, dest_filename))

    if unknown_domains:
        raise ValueError(
            f"Found the following domains that were not in the list of supported domains: {sorted(unknown_domains)}"
        )
    if unknown_intents:
        raise ValueError(
            f"Found the following intents that were not yet in the list of supported intents: {sorted(unknown_intents)}"
        )

    # Validate all of the dataset contents
    _LOGGER.info("Validating fixtures")
    for src_fixture, _ in fixtures:
        validate_fixture(src_fixture)
    _LOGGER.info("Validating intents")
    for src_filename, _ in intent_tests:
        validate_intent_test(src_filename)

    for dest_dir in dest_dirs:
        dest_dir.mkdir(exist_ok=True)

    _LOGGER.info("Copying fixtures")
    for src_fixture, dst_fixture in fixtures:
        shutil.copy2(src_fixture, dst_fixture)

    _LOGGER.info("Copying intent tests")
    for src_intent_test_file, dst_intent_dataset_file in intent_tests:
        try:
            convert_intent_test(src_intent_test_file, dst_intent_dataset_file)
        except ValueError as err:
            raise ValueError(f"Error converting {src_intent_test_file}: {err}") from err
