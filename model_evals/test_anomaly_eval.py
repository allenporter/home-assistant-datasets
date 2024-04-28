"""An evaluation of model base capabilities to classify a summary as an Anomaly."""

from collections.abc import Generator, Callable
import logging
import pathlib
import asyncio
from dataclasses import dataclass
import hashlib
import uuid
import random
import dataclasses

import pytest
from pytest_subtests import SubTests
import yaml

from homeassistant.core import HomeAssistant



from .conftest import ConversationAgent, EvalRecordWriter
from .common import ModelConfig


_LOGGER = logging.getLogger(__name__)

MODEL_EVAL_OUTPUT = "model_outputs/anomaly"
DATASET_FILE = "datasets/anomaly/anomaly.yaml"
VALID_LABELS = ['normal', 'anomaly']

BASE_PROMPT = """
You are a Home Automation Agent that will classify the state of an area of a
home to determine if anything abnormal is happening that should be flagged. You
use your knowledge of the world to understand the difference between the mundane
day-to-day operations of a smart home vs events that are truly abnormal and need
to be investigated.
{examples}

Please respond with a single word answer of 'normal' or 'anomaly' to the
summary.
"""

EVAL_RECORDS_SPLIT = 0.7
EXAMPLE_NUM = {
    "zero-shot": 0,
    "10-shot": 10,
}


@pytest.fixture(
    name="model_id",
    params=[
        "llama3",
        "gemma",
        "mistral-7b-instruct",
        #"gemini-pro",
        #"gpt-3.5",
    ],
)
def model_id_fixture(request: pytest.FixtureRequest) -> str:
    """Fiture that defines which model is being evaluated."""
    return request.param


@pytest.fixture(
    name="prompt_label",
    params=["zero-shot", "10-shot"],
)
def prompt_label_fixture(request: pytest.FixtureRequest) -> str:
    return request.param


@pytest.fixture(name="eval_record_writer")
def eval_record_writer_fixture(
    hass: HomeAssistant,
    model_config: ModelConfig,
    prompt_label: str,
) -> Generator[EvalRecordWriter, None, None]:
    """Fixture that prepares the eval output writer."""
    writer = EvalRecordWriter(
        pathlib.Path(MODEL_EVAL_OUTPUT),
        f"{model_config.model_id}-{prompt_label}.yaml",
    )
    writer.open()
    yield writer
    writer.close()


@dataclass
class LabelTask:
    """Detail about the task that is being evaluated."""

    text: str
    """The summary of the home that is being evaluated."""

    label: str
    """The label assigned to the task."""

    @property
    def task_id(self) -> str:
        """An identifier that labels this area summary evaluation task."""
        m = hashlib.sha256()
        m.update(self.text.encode())
        hash = m.hexdigest()
        return f"{hash}-{self.label}"


@pytest.fixture(name="dataset_records")
def mock_dataset_records() -> list[dict[str, str]]:
    """Fixture to read the dataset yaml contennts."""
    with pathlib.Path(DATASET_FILE).absolute().open("r") as f:
        content = f.read()
    dataset = yaml.load(content, Loader=yaml.Loader)
    records = dataset["records"]
    _LOGGER.info("Loaded %s records to evaluate", len(records))
    random.shuffle(records)
    return records


@pytest.fixture(name="eval_split")
def mock_eval_records(dataset_records: list[dict[str, str]]) -> list[dict[str, str]]:
    """Fixture to read the dataset yaml contennts."""
    return dataset_records[:int(EVAL_RECORDS_SPLIT * len(dataset_records))]


@pytest.fixture(name="fewshot_split")
def mock_fewshot_records(dataset_records: list[dict[str, str]]) -> list[dict[str, str]]:
    """Fixture to read the dataset yaml contennts."""
    return dataset_records[int(EVAL_RECORDS_SPLIT * len(dataset_records)):]


@pytest.fixture(name="tasks_provider")
def tasks_provider_fixture(
    hass: HomeAssistant,
    eval_split: list[dict[str, str]],
) -> Callable[[], Generator[LabelTask, None, None]]:
    """Fixture that generates the tasks to evaluate."""

    _LOGGER.info("Loaded %s areas to evaluate", len(eval_split))

    def func() -> Generator[LabelTask, None, None]:
        for record in eval_split:
            yield LabelTask(
                text=record["summary"],
                label=record["label"],
            )

    return func



@pytest.fixture(name="system_prompt")
def mock_system_prompt(prompt_label: str, fewshot_split: list[dict[str, str]]) -> list[dict[str, str]]:
    """Fixture to read the dataset yaml contennts."""
    records = fewshot_split
    random.shuffle(records)

    example_num = EXAMPLE_NUM[prompt_label]
    examples = "\n".join(
        f"Text: {record['summary']}\nLabel: {record['label']}"
        for record in records[:example_num]
    )
    return BASE_PROMPT.format(examples=examples)


async def test_collect_area_summaries(
    hass: HomeAssistant,
    agent: ConversationAgent,
    eval_record_writer: EvalRecordWriter,
    subtests: SubTests,
    tasks_provider: Callable[[], Generator[LabelTask, None, None]],
) -> None:
    """Collects model responses for area summaries."""

    for i, task in enumerate(tasks_provider()):
        with subtests.test(msg=task.task_id, i=i):

            # Run the conversation agent
            _LOGGER.info("Processing task: %s", task.text)
            response = await agent.async_process(hass, task.text)
            _LOGGER.debug("Response: %s", response)

            # Cleanup the response in case there are small text variations
            response = response.lower().lstrip()
            if response not in VALID_LABELS:
                for valid_label in VALID_LABELS:
                    if response.startswith("Label: "):
                        response = response[7:]
                    if response.startswith(valid_label):
                        response = valid_label
                        break

            eval_record_writer.write(
                {
                    "uuid": str(uuid.uuid4()),  # Unique based on the model evaluated
                    "task_id": task.task_id,
                    "task": dataclasses.asdict(task),
                    "response": response,
                }
            )
