"""Tests for the scrape_reader module."""

import pathlib

from home_assistant_datasets.metrics.scrape_reader import model_output_files


TESTDATA = pathlib.Path("tests/metrics/testdata/")


def test_model_output_files() -> None:
    """Test for model_output_files."""

    files = model_output_files(TESTDATA)
    assert [file.name for file in files] == [
        "door_left_open_door_left_open-door_left_open-0.yaml",
        "humidity_fan_humidity_fan-humidity_fan-0.yaml",
        "light_on_door_light_on_door-light_on_door-0.yaml",
        "vacuum_pause_vacuum_pause-vacuum_pause-0.yaml",
    ]


def test_model_output_files_task_id() -> None:
    """Test for model_output_files with a task id."""

    files = model_output_files(TESTDATA, task_id="vacuum_pause")
    assert [file.name for file in files] == [
        "vacuum_pause_vacuum_pause-vacuum_pause-0.yaml",
    ]
