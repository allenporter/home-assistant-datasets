# Dataset
## Responsibility

Convert home-assistant-datasets into stateful, tool-decision training data.

This is where the real suffering happens.

⸻

## Deliverables

1. Conversion Plan (conversion_plan.md)

Must specify:
	•	How ontology is injected
	•	How aliases are applied
	•	How state-fetch vs action examples are generated
	•	How multi-turn examples are produced

⸻

2. Validation Rules (validation.md)

Must check:
	•	JSON validity
	•	Schema compliance
	•	Tool correctness
	•	Entity ID validity
	•	Alias resolution coverage
	•	No hallucinated IDs

⸻

## Hard Rules
	•	No freeform assistant text unless explicitly allowed
	•	All outputs must be parseable
	•	More negative examples than positive

⸻

## Success Criteria
	•	Dataset can be trained without runtime parsing failures
	•	Tool overcalling is statistically suppressed
