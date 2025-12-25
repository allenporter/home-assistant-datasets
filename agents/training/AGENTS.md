# Training
## Responsibility

Define how Qwen3 is fine-tuned.

This agent does not touch datasets or schemas.

⸻

## Deliverables

1. Fine-Tuning Plan (finetune_plan.md)

Must include:
	•	Base model selection
	•	LoRA config
	•	Target modules
	•	Batch/accumulation strategy
	•	Tokenization rules
	•	Packing strategy

⸻

## Hard Rules
	•	No function calling APIs
	•	No RL
	•	No chain-of-thought exposure
	•	Strict JSON outputs only

⸻

## Success Criteria
	•	Model emits correct tool decisions on held-out states
	•	No schema drift after fine-tune
