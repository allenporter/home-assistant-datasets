"""Library for computing metrics related to eval costs."""

from collections.abc import Generator
from dataclasses import dataclass
import pathlib

import yaml

from home_assistant_datasets.models import read_models, Cost


TOKEN_STATS_FILE = "reports-token-stats.yaml"


@dataclass
class EvalCost:
    """Evaluation cost metrics for a model."""

    input_tokens: int
    """Total number of input tokens."""

    output_tokens: int
    """Total number of output tokens."""

    avg_latency_ms: int
    """Average latency (ms)"""

    model_rates: Cost
    """Model pricing."""

    @property
    def input_token_rate(self) -> float:
        """Rate for $/1M input tokens."""
        return self.model_rates.input_tokens * 1.0

    @property
    def output_token_rate(self) -> float:
        """Rate for $/1M output tokens."""
        return self.model_rates.output_tokens * 1.0

    @property
    def total_eval_cost(self) -> float:
        """Total eval cost in $."""
        return self.input_token_rate * (
            self.input_tokens / 1_000_000
        ) + self.output_token_rate * (self.output_tokens / 1_000_000)


# Read token stats file which is in a format like this:
# - model_id: gemini-1.5-flash
#   token_avg:
#       duration_ms: 1016.12
#   token_sum:
#       input_tokens: 6015352
#       output_tokens: 51588
def token_stats(
    assist_report_dir: pathlib.Path,
) -> Generator[tuple[str, int, int, int], None, None]:
    """Generate the set of models and input and output token costs, plus latency."""
    for token_stats_file in sorted(
        list(assist_report_dir.glob(f"**/{TOKEN_STATS_FILE}"))
    ):
        data = yaml.load(token_stats_file.open(), Loader=yaml.Loader)
        for model_info in data:
            if not (model_id := model_info.get("model_id")):
                continue
            token_sum = model_info["token_sum"]
            in_t = int(token_sum["input_tokens"])
            out_t = int(token_sum["output_tokens"])
            token_avg = model_info["token_avg"]
            duration_ms = int(token_avg["duration_ms"])
            yield model_id, in_t, out_t, duration_ms


def compute_model_eval_cost(assist_report_dir: pathlib.Path) -> dict[str, EvalCost]:
    """Determine the evaluation costs for each model."""

    # Build up rates for each model
    model_costs: dict[str, Cost] = {
        model.model_id: model.cost
        for model in read_models().models
        if model.cost is not None
    }

    eval_costs = {}
    for model_id, input_tokens, output_tokens, avg_latency_ms in token_stats(
        assist_report_dir
    ):
        if not (model_rate := model_costs.get(model_id)):
            continue
        eval_costs[model_id] = EvalCost(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            avg_latency_ms=avg_latency_ms,
            model_rates=model_rate,
        )
    return eval_costs
