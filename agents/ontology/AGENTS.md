# Ontology
## Responsibility

Define and maintain the static home ontology.

This includes:
	•	Floors → Rooms → Devices → Entities
	•	Capabilities
	•	Units
	•	Aliases
	•	Stable IDs
	•	Schema versioning

This agent never handles dynamic state.

⸻

## Deliverables

1. Ontology Schema (schema.json)

Must define:
	•	Deterministic key order
	•	Required fields
	•	Alias lists
	•	Capability lists

Must be:
	•	Additive-only (no removals)
	•	Backward compatible

⸻

2. Canonical Examples (examples.json)

At least:
	•	1 minimal house
	•	1 multi-room setup
	•	1 alias-heavy example
	•	1 ambiguous-alias example

⸻

## Hard Rules
	•	No dynamic values
	•	No presence flags here
	•	No nulls except for units
	•	IDs are immutable once introduced

⸻

## Success Criteria
	•	Given a user utterance, another agent can resolve entity IDs without guessing
	•	Ontology diffing does not require retraining