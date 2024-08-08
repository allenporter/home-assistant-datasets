# Change Log

This is a work log of major updates to the leaderboard.

## 2024-08-08

Reports that many ollama context sizes are defaulting to well below what the model supports
and all local llm benchmarks need to be re-run.

- lama3.1 `assist` performance went from 45% to 66% with 8k context size
- xlam-7b `assist` performance went from 25% to 50% with 4k context size

Still need to update other models (xlam 1b, llama3-groq-tool-use, mistral, etc)
