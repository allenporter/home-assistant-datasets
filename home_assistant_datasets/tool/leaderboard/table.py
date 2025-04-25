"""Library for creating simple markdown tables."""

from home_assistant_datasets.datasets.dataset_card import DatasetCard
from home_assistant_datasets.models import ModelConfig

from .eval_cost import EvalCost


CARD_MARKDOWN = """
### {name}

{description}

{eval_cost}

More information:
{urls}
"""

EVAL_COST = """
#### Assist Eval Performance Metrics

- Average Latency: {eval_cost.avg_latency_ms} (ms)
- Total Eval Cost: ${eval_cost.total_eval_cost:0.2f}
- Cost breakdown:
    - {eval_cost.input_tokens} input tokens, ${eval_cost.model_rates.input_tokens:0.2f}/1M tokens
    - {eval_cost.output_tokens} output tokens, ${eval_cost.model_rates.output_tokens:0.2f}/1M tokens

{eval_cost.model_rates.notes}
"""


def format_dataset_card(dataset_card: DatasetCard) -> str:
    """Format a dataset card."""
    return CARD_MARKDOWN.format(
        name=dataset_card.name,
        eval_cost="",
        description=dataset_card.description,
        urls="\n".join(f"- {url}" for url in dataset_card.urls),
    )


def format_model_card(model_card: ModelConfig, eval_cost: EvalCost | None = None) -> str:
    """Format a dataset card."""
    eval_cost_str = ""
    if eval_cost is not None:
        eval_cost_str = EVAL_COST.format(eval_cost=eval_cost)
    return CARD_MARKDOWN.format(
        name=model_card.model_id,
        description=model_card.description,
        eval_cost=eval_cost_str,
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
