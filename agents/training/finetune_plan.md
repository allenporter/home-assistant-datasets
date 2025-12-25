# Finetune Plan
## Purpose

This document defines how Qwen3 is fine-tuned for state-conditioned tool-calling in Home Assistant.

It explicitly defines:
	•	What is trained
	•	What is not trained
	•	What data shape is expected
	•	What constitutes success or failure

Anything not written here is out of scope.

⸻

## Model Scope

Base Model
	•	Model family: Qwen3
	•	Supported sizes (initially):
	•	Qwen/Qwen3-1.7B
	•	Qwen/Qwen3-4B
	•	MoE variants are explicitly excluded in v0

Rationale: dense models are predictable; MoE introduces routing variance that complicates tool decision learning.

⸻

## Fine-Tuning Method

Technique
	•	LoRA (Low-Rank Adaptation)
	•	No full-parameter fine-tuning
	•	No RLHF
	•	No preference optimization
	•	No function-calling APIs

This is supervised learning. We are teaching pattern recognition, not enlightenment.

⸻

## Target Modules

LoRA is applied to the following modules only:

```
q_proj
k_proj
v_proj
o_proj
gate_proj
up_proj
down_proj
```

Bias terms are not trained.

Rationale:
These modules control attention and feed-forward routing, which directly affect:
	•	tool vs text decision
	•	action ordering
	•	state sensitivity

⸻

## Input Format (Strict)

Each training example MUST be formatted as:
```
System:
  ONTOLOGY: <static ontology JSON>
  [STATE: <dynamic state JSON>]

User:
  <natural language command>

Assistant:
  <either JSON tool call(s) OR plain text>
```

Rules:
	•	Ontology is always present
	•	State is present only if fetched
	•	No hidden chain-of-thought
	•	No assistant commentary before or after JSON
	•	Tool calls are emitted as raw JSON, one per line if multiple

⸻

## Output Classes

The model is trained to produce exactly one of the following:

1. State Fetch Tool Call

```json
{"tool_call":{"name":"get_entity_state","arguments":{"entity_ids":["movie_room_tv"]}}}
```

Used when:
	•	Required state is missing
	•	Action legality depends on state

⸻

2. Action Tool Calls (Ordered)

```jsonl
{"tool_call":{"name":"tv_power","arguments":{"entity_id":"movie_room_tv","state":"on"}}}
{"tool_call":{"name":"tv_input","arguments":{"entity_id":"movie_room_tv","input":"plex"}}}
{"tool_call":{"name":"plex_play","arguments":{"title":"Terminator"}}}
```

Rules:
	•	Order matters
	•	No redundant actions
	•	No actions on present:false entities

⸻

3. Plain Text Response

Used only for:
	•	Clarification questions
	•	Refusals due to ambiguity or missing entities
	•	Explicit no-ops

Plain text must not resemble JSON.

⸻

## Dataset Composition Requirements

Required Ratios (v0)
	•	50–70% examples produce no tool calls
	•	20–40% produce exactly one tool call
	•	≤10% produce multi-step sequences

This prevents tool over-calling and “agent enthusiasm”.

⸻

## Required Coverage

Dataset MUST include:
	•	Alias resolution (same entity, different names)
	•	Same user command with different states → different plans
	•	Present=false entities → refusal or clarification
	•	Already-satisfied state → minimal action
	•	Missing state → state fetch

If any of these are missing, training is invalid.

⸻

## Training Configuration (Baseline)

Suggested Defaults (v0)
	•	Max sequence length: 2048
	•	Batch size: 1
	•	Gradient accumulation: 8
	•	Learning rate: 2e-4
	•	Epochs: 1–2
	•	Optimizer: adamw_torch
	•	Precision: bf16 (GPU permitting)
	•	Packing: enabled

These are not sacred. They are known-not-terrible.

⸻

## What Is Explicitly NOT Trained
	•	World knowledge
	•	Conversational tone
	•	Memory across turns
	•	Natural language reasoning
	•	Implicit state inference

If the model “remembers” something, that is a bug.

⸻

## Evaluation Criteria

Training is considered successful if:
	1.	Tool decision accuracy
	•	Correctly chooses fetch vs act vs no-op
	2.	Action minimality
	•	Does not emit redundant tool calls
	3.	State sensitivity
	•	Same command, different state → different output
	4.	Schema compliance
	•	All tool calls validate against v0 schemas
	5.	No hallucinated IDs
	•	Every entity ID exists in ontology

If any fail, retraining is not the solution. Dataset is.

⸻

## Versioning & Compatibility
	•	This plan targets v0 schemas only
	•	Schema evolution must be additive
	•	New schema versions require:
	•	New training data
	•	Explicit opt-in

No silent upgrades.

⸻

## Exit Criteria

v0 fine-tuning is complete when:
	•	A held-out evaluation set passes all criteria
	•	Multi-turn execution behaves deterministically
	•	No manual prompt hacks are required

At that point, move to v1.

⸻

### Closing Note (read this twice)

If behavior is wrong:
	•	Do not increase epochs
	•	Do not tweak LoRA rank
	•	Do not add “just one more prompt”

Fix the dataset.

This document exists so we don’t argue about this later.
