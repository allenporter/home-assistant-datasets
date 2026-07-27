"""Functions for testing the internals of the leaderboard chart creation."""

from home_assistant_datasets.tool.leaderboard import chart


def test_empty_color_map() -> None:
    """Test creating a color map for a set of values."""


def test_color_map() -> None:
    """Test creating a color map for a set of values."""

    assert chart.color_map(["key-a", "key-b"]) == {
        "key-a": "#4285f4",
        "key-b": "#0f9d58",
    }
    assert chart.color_map(["key-a", "key-b", "key-c"]) == {
        "key-a": "#4285f4",
        "key-b": "#0f9d58",
        "key-c": "#f4b400",
    }


def test_wrap_colors() -> None:
    """Test creating a color map for a set of values."""
    assert chart.color_map(f"key-{v:02d}" for v in range(0, 15)) == {
        "key-00": "#4285f4",
        "key-01": "#0f9d58",
        "key-02": "#f4b400",
        "key-03": "#ea4335",
        "key-04": "#fbbc04",
        "key-05": "#34a853",
        "key-06": "#ff6d01",
        "key-07": "#46bdc6",
        "key-08": "#1155cc",
        "key-09": "#d5a6bd",
        "key-10": "#6aa84f",
        "key-11": "#674ea7",
        "key-12": "#d9ead3",
        # Wrap
        "key-13": "#4285f4",
        "key-14": "#0f9d58",
    }


def test_model_xy_chart() -> None:
    """Test creating a model xy chart."""
    models = ["model-a", "model-b"]
    dataset_chart = chart.DatasetChart(
        dataset="My Title", models=models, scores=[50, 75]
    )
    assert (
        chart.model_xy_chart(dataset_chart, model_colors=chart.color_map(models))
        == """```mermaid
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
            plotColorPalette: "#4285f4, #0f9d58"

---
xychart-beta
  title "My Title"
  x-axis "Model" [model-a, model-b]
  y-axis "Score" 1 --> 100
  bar [50.0, 0.0]
  bar [0.0, 75.0]
```"""
    )
