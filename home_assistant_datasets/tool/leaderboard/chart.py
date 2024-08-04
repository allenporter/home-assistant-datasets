"""Library for working with chart values."""

from dataclasses import dataclass
from collections.abc import Iterable
import itertools

import numpy as np

_COLORS = [
    "#4285f4",
    "#0f9d58",
    "#f4b400",
    "#ea4335",
    "#fbbc04",
    "#34a853",
    "#ff6d01",
    "#46bdc6",
    "#1155cc",
    "#d5a6bd",
    "#6aa84f",
    "#674ea7",
    "#d9ead3",
]


def color_map(keys: Iterable[str]) -> dict[str, str]:
    """Create a map of keys to colors."""
    return {key: color for key, color in zip(keys, itertools.cycle(_COLORS))}


@dataclass
class DatasetChart:
    """Input into an XYChart."""

    dataset: str
    models: list[str]
    scores: list[float]


THEME_INIT = "%%{{init: {'themeCSS': '.mermaid .tick > text {rotate: -45deg; text-anchor: end !important;}' }}%%"

def model_xy_chart(chart: DatasetChart, model_colors: dict[str, str]) -> str:
    """Return markdown for an XYChart."""
    x_axis_str = ", ".join(chart.models)
    color_str = ", ".join(model_colors[model_id] for model_id in chart.models)
    bar_diagonal_values = np.zeros((len(chart.models), len(chart.models)))
    np.fill_diagonal(bar_diagonal_values, chart.scores)
    bar_str = "\n".join(
        [
            f"  bar [{", ".join([ f"{cell:0.1f}" for cell in row ])}]"
            for row in bar_diagonal_values
        ]
    )
    return f"""```mermaid
{THEME_INIT}
---
config:
    xyChart:
        width: 1500
        height: 800
        xAxis:
          labelFontSize: 12
          labelPadding: 8
    themeVariables:
        xyChart:
            titleColor: "#ff0000"
            plotColorPalette: "{color_str}"

---
xychart-beta
  title "{chart.dataset}"
  x-axis "Model" [{x_axis_str}]
  y-axis "Score" 1 --> 100
{bar_str}
```"""
