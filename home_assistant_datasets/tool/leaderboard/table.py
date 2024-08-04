"""Library for creating simple markdown tables."""


def table(cols: list[str], rows: list[list[str]]) -> str:
    """Create a markdown table"""
    results = [
        ["| ", " | ".join(cols), " |"],
        ["| --- " * len(cols), "|"],
        *["".join(["| ", " | ".join(row), " |"]) for row in rows],
    ]
    return "\n".join(["".join(result) for result in results])
