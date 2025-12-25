# State
## Responsibility

Define dynamic entity state representation and rules.

This agent does not define ontology or tools.

⸻

## Deliverables

1. State Schema (schema.json)

Must include:
	•	present flag
	•	All attributes defined in ontology
	•	Explicit nulls
	•	Schema version

⸻

## 2. Example States (examples.json)

At least:
	•	Fully present entity
	•	Present=false entity
	•	Partially unknown entity
	•	Multi-entity snapshot

⸻

## Hard Rules
	•	Never omit attributes
	•	Never infer values
	•	Never collapse nulls into presence
	•	State is always authoritative

⸻

## Success Criteria
	•	Model behavior changes solely based on state changes
	•	Multiturn execution does not repeat actions