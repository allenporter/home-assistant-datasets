"""Module for converting intent test fixtures to assist dataset format."""

import datetime
import pathlib
import logging
from typing import Any

import yaml
from synthetic_home import inventory
from tqdm import tqdm

from home_assistant_datasets.datasets.dataset_card import DatasetCard, DATASET_CARD_FILE
from home_assistant_datasets.datasets.assist_data_loader import (
    Record,
    Action,
    ToolCall,
)

__all__ = [
    "convert_intent_tests",
]


def now() -> datetime.datetime:
    """For mocking for tests."""
    return datetime.datetime.now()


def _create_dataset_card() -> DatasetCard:
    """For mocking for tests."""
    return DatasetCard(
        name="intents",
        description=f"""
A dataset built form the Home Assistant intents repo, modeled after existing
NLP test cases for the assistant pipeline.

This dataset has been adapted for evaluating the Home Assistant LLM API ([blog post](https://developers.home-assistant.io/blog/2024/05/20/llm-api/))
imported from the home assistant intents repo.

This is mean to reuse the tests that already exist for the NLP, which turns out
to expose some weaknesses or differences of interpretation of tasks. It also is
a very large home which is challenging for smaller models given the ~100 or so
devices. Lastly, there are some tests that have subtle mismatches that are reasonable (e.g.
"minimum brightness" tests)

This dataset uses the `assist` format. See the `assist` dataset card and README for
additional details about the format and information about running the evaluation.

Updated: {now().isoformat()}
""",
        urls=[
            "https://github.com/allenporter/home-assistant-datasets/tree/main/datasets/intents",
            "https://github.com/allenporter/home-assistant-datasets/tree/main/datasets/assist",
            "https://github.com/home-assistant/intents",
        ],
    )


_LOGGER = logging.getLogger(__name__)

FIXTURES_FILE = "_fixtures.yaml"

# All domains must be explicitly marked as in or out.
SUPPORTED_DOMAINS = {
    "cover",
    "binary_sensor",
    "climate",
    "fan",
    "homeassistant",
    "light",
    "lock",
    "media_player",
    "sensor",
    "shopping_list",
    "todo",
    "vacuum",
    "valve",
}
UNSUPPORTED_DOMAINS = {
    "_test",
    "assist_satellite",
    "person",
    "weather",  # TODO: Can this be supported?
    # TODO: Add support for these to synthetic_home
    "scene",
    "script",
}

# All domains must be explicitly supported or unsupported.
SUPPORTED_INTENTS = {
    "HassTurnOn",
    # TODO: Confirm if the get / set temperature calls are actually supported
    "HassClimateGetTemperature",
    "HassClimateSetTemperature",
    "HassLightSet",
    "HassListAddItem",
    "HassListCompleteItem",
    "HassMediaNext",
    "HassMediaPause",
    "HassMediaPrevious",
    "HassMediaUnpause",
    "HassSetPosition",
    "HassSetVolume",
    "HassTurnOff",
    "HassVacuumReturnToBase",
    "HassVacuumStart",
}
UNSUPPORTED_INTENTS = {
    # LLMs don't use GetState tool.
    "HassGetState",
    # We only support 'todo' platform entities
    "HassShoppingListAddItem",
    "HassShoppingListCompleteItem",
    # TODO: Support timers
    "HassCancelAllTimers",
    "HassCancelTimer",
    "HassDecreaseTimer",
    "HassIncreaseTimer",
    "HassStartTimer",
    "HassTimerStatus",
    "HassUnpauseTimer",
    # Other requests that are not supported
    "HassGetCurrentDate",
    "HassGetCurrentTime",
    "HassNevermind",
    "HassPauseTimer",
    "HassRespond",
}


def fixture_filename_parts(filename: pathlib.Path) -> tuple[str, str]:
    """Extract the entity domain and intent under test."""
    parts = filename.stem.rsplit("_", maxsplit=1)
    return (parts[0], parts[1])


def convert_intent_to_tool_call(intent: dict[str, Any]) -> ToolCall:
    """Convert an intent test expected intent to an expected tool call."""
    if not (name := intent.get("name")):
        raise ValueError("Intent call missing 'name' field")
    slots = intent.get("slots") or None
    return ToolCall(tool_name=name, tool_args=slots)


def convert_fixture(
    src_fixture: pathlib.Path,
    dst_fixture: pathlib.Path,
) -> None:
    inv = inventory.load_inventory(src_fixture)
    if not (inv.entities or inv.devices or inv.areas):
        raise ValueError(
            f"Fixtures filename {str(src_fixture)} contained no home resources"
        )
    # Filter unsupported domains
    inv.entities = [
        entity
        for entity in inv.entities
        if entity.id is not None
        and (domain := entity.id.split(".", maxsplit=1)[0])
        and domain in SUPPORTED_DOMAINS
    ]
    write_record(inv, dst_fixture)


def convert_intent_test(intent_test_file: pathlib.Path) -> Record | None:
    """Convert a single intent test file to an intents assist dataset."""
    domain, _ = fixture_filename_parts(intent_test_file)
    content = yaml.load(intent_test_file.open(), Loader=yaml.Loader)
    actions: list[Action] = []
    for test in content.get("tests") or []:
        if not (sentences := test["sentences"]):
            continue
        expect_response: str | list[str] | None = None
        if response := test.get("response"):
            if isinstance(response, str) or isinstance(response, list):
                expect_response = response
            else:
                raise ValueError(
                    f"Unknown 'response' type, expected str or list: {response}"
                )
        tool_call = convert_intent_to_tool_call(test["intent"])
        action = Action(
            sentences=sentences,
            expect_response=expect_response,
            expect_tool_call=tool_call,
        )
        actions.append(action)
    if not actions:
        _LOGGER.debug("Skipping intent with no actions")
        return None
    return Record(
        category=[domain],
        tests=actions,
    )


def write_record(
    record: Record | inventory.Inventory, intent_dataset_file: pathlib.Path
) -> None:
    """Write the record file to the destination."""
    intent_dataset_file.write_text(
        yaml.dump(
            record.to_dict(omit_none=True),
            sort_keys=False,
            explicit_start=True,
            allow_unicode=True,
        )
    )


def validate_fixture(filename: pathlib.Path) -> None:
    """Validate the fixture path is valid."""
    # Verify the inventory file is valid
    inv = inventory.load_inventory(filename)
    if not (inv.entities or inv.devices or inv.areas):
        raise ValueError(
            f"Fixtures filename {str(filename)} contained no home resources"
        )


def supported_files(
    intents_test_subdir: pathlib.Path,
    unknown_domains: set,
    unknown_intents: set,
) -> tuple[str | None, list[str]]:
    """Get the supported files from the subdirectory.

    Returns a tuple of fixture filenames and test filenames. Populates the
    list of unknown_domains and unnnkown_intents
    """
    fixture: str | None
    intents: list[str] = []
    for filename in intents_test_subdir.iterdir():
        if filename.name == FIXTURES_FILE:
            fixture = filename.name
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
            continue
        intents.append(filename.name)
    return (fixture, intents)


def convert_intent_tests(
    intent_tests_path: pathlib.Path,
    intents_dataset_path: pathlib.Path,
    progress: tqdm | None = None,
) -> None:
    """Convert a directory of intent tests to an intents assist dataset."""

    if not intent_tests_path.is_dir():
        raise ValueError(f"Intents test path {intent_tests_path} is not a directory")

    intents_dataset_path.mkdir(exist_ok=True)

    # Source subdir, destination subdir, fixture file, and list of intent tests
    mappings: list[tuple[pathlib.Path, pathlib.Path, str, list[str]]] = []
    unknown_domains: set[str] = set()
    unknown_intents: set[str] = set()
    for subdir in intent_tests_path.iterdir():
        if not subdir.is_dir():
            continue
        fixture, intents = supported_files(subdir, unknown_domains, unknown_intents)
        if not fixture or not intents:
            continue
        dest_path = intents_dataset_path / subdir.name
        mappings.append((subdir, dest_path, fixture, intents))

    if unknown_domains:
        raise ValueError(
            f"Found the following domains that were not in the list of supported domains:\n{'\n'.join(sorted(unknown_domains))}"
        )
    if unknown_intents:
        raise ValueError(
            f"Found the following intents that were not yet in the list of supported intents:\n{'\n'.join(sorted(unknown_intents))}"
        )

    # Validate all of the dataset contents
    _LOGGER.info("Validating fixtures")

    if progress is not None:
        progress.set_description("Validating fixtures")
        progress.total = len(mappings)
    for mapping in mappings:
        src_path, _, fixture_name, _ = mapping
        validate_fixture(src_path / fixture_name)
        if progress is not None:
            progress.update()

    if progress is not None:
        progress.clear()
        progress.set_description("Copying intents")
        progress.total = len(mappings)
    for mapping in mappings:
        src_path, dst_path, fixture_name, test_file_names = mapping
        records_to_write: list[tuple[pathlib.Path, Record]] = []
        for test_file in test_file_names:
            intent_test_file = src_path / test_file
            if not (record := convert_intent_test(intent_test_file)):
                continue
            dst_record_file = dst_path / test_file
            records_to_write.append((dst_record_file, record))
        if not records_to_write:
            continue
        dst_path.mkdir(exist_ok=True)

        # Write dataset records
        for record_file, record in records_to_write:
            write_record(record, record_file)

        # Convert fixture
        convert_fixture(src_path / fixture_name, dst_path / fixture_name)

        if progress is not None:
            progress.update()

    if progress is not None:
        progress.clear()

    dataset_card_file = intents_dataset_path / DATASET_CARD_FILE
    _LOGGER.info("Writing dataset card: %s", str(dataset_card_file))
    dataset_card_file.write_text(
        yaml.dump(
            _create_dataset_card().to_dict(),
            sort_keys=False,
            explicit_start=True,
            allow_unicode=True,
        )
    )
