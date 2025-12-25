# Tools
## Responsibility

Define tool schemas and semantics.

This includes:
	•	State fetch tools
	•	Action tools
	•	Validation expectations

This agent does not define prompts or training logic.

⸻

## Deliverables

1. Tool Schemas (schemas/*.json)

Required tools:
	•	get_entity_state
	•	One tool per capability (tv_power, tv_input, media_play, etc.)

⸻

2. Tool Examples (examples.json)

Include:
	•	Valid calls
	•	Invalid calls
	•	Edge cases (missing entity, present=false)

⸻

## Hard Rules
	•	Tool schemas are strict
	•	No optional arguments unless unavoidable
	•	No tool chaining logic here

⸻

## Success Criteria
	•	Tool outputs are machine-validated
	•	Model never invents arguments