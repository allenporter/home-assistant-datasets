# Change Log

This is a work log of major updates to the leaderboard.

## 2024-09-02

- claude-3.5-sonnet `assist-mini` scores 95%
- claude-3-haiku `assist-mini` scores 98%

## 2024-08-08

Reports that many ollama context sizes are defaulting to well below what the model supports
and all local llm benchmarks need to be re-run.

- llama3.1 `assist` performance went from 45% to 66% with 8k context size
- llama3.1 `intents` performance went from 22% to 43% with 8k content size
- xlam-7b `assist` performance went from 25% to 50% with 4k context size

Still need to update other models (xlam 1b, llama3-groq-tool-use, mistral, etc)
