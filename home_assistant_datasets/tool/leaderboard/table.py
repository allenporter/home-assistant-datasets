"""Library for creating simple markdown tables."""

from home_assistant_datasets.datasets.dataset_card import DatasetCard
from home_assistant_datasets.models import ModelConfig


CARD_MARKDOWN = """
### {name}

{description}

More information:
{urls}
"""


def format_dataset_card(dataset_card: DatasetCard) -> str:
    """Format a dataset card."""
    return CARD_MARKDOWN.format(
        name=dataset_card.name,
        description=dataset_card.description,
        urls="\n".join(f"- {url}" for url in dataset_card.urls),
    )


def format_model_card(model_card: ModelConfig) -> str:
    """Format a dataset card."""
    return CARD_MARKDOWN.format(
        name=model_card.model_id,
        description=model_card.description,
        urls="\n".join(f"- {url}" for url in model_card.urls or ()),
    )


def table(cols: list[str], rows: list[list[str]]) -> str:
    """Create a markdown table"""
    results = [
        ["| ", " | ".join(cols), " |"],
        ["| --- " * len(cols), "|"],
        *["".join(["| ", " | ".join(row), " |"]) for row in rows],
    ]
    return "\n".join(["".join(result) for result in results])
