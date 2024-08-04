"""Library for creating simple markdown tables."""

from home_assistant_datasets import data_model


DATASET_CARD_MARKDOWN = """
## {dataset_card.name}

{dataset_card.description}

More information:
{urls}
"""


def format_dataset_card(dataset_card: data_model.DatasetCard) -> str:
    """Format a dataset card."""
    return DATASET_CARD_MARKDOWN.format(
        dataset_card=dataset_card,
        urls="\n".join(
            f"- {url}"
            for url in dataset_card.urls
        )
    )


def table(cols: list[str], rows: list[list[str]]) -> str:
    """Create a markdown table"""
    results = [
        ["| ", " | ".join(cols), " |"],
        ["| --- " * len(cols), "|"],
        *["".join(["| ", " | ".join(row), " |"]) for row in rows],
    ]
    return "\n".join(["".join(result) for result in results])
