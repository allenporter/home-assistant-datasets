# Inference Runtime Contract (v0)

## Input
Each inference turn receives:
1. Full static ontology (unchanged)
2. Optional dynamic state snapshot
3. Current user utterance

## Output
The model may emit:
- One or more JSON tool calls (one per line)
- A clarification or refusal message (plain text)

## Rules
- Tool calls must validate against v0 tool schemas
- Outputs are executed in order
- State is refreshed after tool execution
- Model output is never treated as authoritative state

## Error Handling
- Invalid tool calls are rejected
- Partial execution failures halt the sequence
- The next turn receives updated state