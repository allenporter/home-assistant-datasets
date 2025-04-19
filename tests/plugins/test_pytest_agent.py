"""Tests for the conversation agent pytest plugin."""

from typing import Any
import pathlib
from unittest.mock import patch

from syrupy import SnapshotAssertion

from home_assistant_datasets.models import read_model
from home_assistant_datasets.datasets.dataset_card import read_dataset_card

# Loading these has the effect of caching them so the calls work inside of
# pytesster. This is a bit of a hack, but leaving since its less code than
# copy all the files into the environment.
with patch("home_assistant_datasets.secrets.get_secret", return_value="SECRET"):
    _MODEL_CONFIG = read_model("assistant")
_DATASET_CARD = read_dataset_card(pathlib.Path("datasets/assist/"))

PYTEST_ARGS = ["--dataset", "datasets/assist"]
PLUGINS = [
    "home_assistant_datasets.plugins.pytest_dataset",
    "home_assistant_datasets.plugins.pytest_agent",
]
PYTEST_INI = """
[pytest]
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
"""

TEST_FILE_CONTENTS = """
    import pytest

    from homeassistant.core import HomeAssistant

    from home_assistant_datasets.agent import ConversationAgent

    @pytest.fixture(name="model_id", scope="module")
    def model_id_fixture() -> str:
        return "assistant"

    async def test_agent(hass: HomeAssistant, agent: ConversationAgent) -> None:
        response = await agent.async_process(hass, "What is the capital of France?")
        assert response == "Sorry, I am not aware of any device called capital of France"
"""


def test_pytest_agent(pytester: Any, snapshot: SnapshotAssertion) -> None:
    """Exercise the report plugin."""

    pytester.makepyfile(TEST_FILE_CONTENTS)
    pytester.makeini(PYTEST_INI)

    result = pytester.runpytest(*PYTEST_ARGS, plugins=PLUGINS)
    stdout = "\n".join(result.stdout.lines)
    assert "1 passed" in stdout
