# Robam-Shishen-HomeMind: questions

Robam-Shishen-HomeMind is a smart-home assistant model developed by the large-model team at ROBAM, as part of the Shishen model family.

Official URL: https://www.robam.com/roki/index

## Evaluation details

- Organization: ROBAM large-model team, Shishen model family.
- Base model: Qwen3.6-35B-A3B, adapted with LoRA supervised fine-tuning.
- Selected checkpoint: two epochs, internal identifier checkpoint-192.
- Inference: vLLM 0.19.1, BF16, tensor parallelism 2, thinking disabled, qwen3_xml tool parser.
- Home Assistant: 2026.10.2. Integration: vicuna_conversation.
- Dataset scores: assist 438/460, assist-mini 196/196, questions 360/370. Aggregate 994/1026 (96.88%).
- The model configuration contains a placeholder OpenAI-compatible local endpoint, not a public API service.

## Training and checkpoint selection

Training included public Home Assistant benchmark scenarios and paraphrases. The same benchmark was used for checkpoint selection. These are local development-benchmark results, not independent held-out test results.

## Output provenance and scoring scope

The original collection used the internal served-model alias `qwen36-auto-r01-checkpoint-192`. The reporting model identifier is now `Robam-Shishen-HomeMind`. Task inputs, predictions, tool histories, and recorded state differences are preserved. The original alias is recorded in each output's context. Local absolute paths and the operator name were removed from scrape metadata.

The original collector generates colliding task filenames for some distinct setup/device-context scenarios. In particular, `Set the volume to 0%` has three contexts sharing five filenames. The historical baseline's final files for those IDs have no scoring criteria, while parallel collection can retain a context with scoring criteria. The submitted assist cohort is fixed to the 460 scoring task IDs in the historical baseline. Its membership is identical across baseline and candidate; no selection by pass/fail outcome was performed. Original complete scenario archives remain available internally. This scope and the collector collision should be reviewed by the maintainers before accepting the score.

The benchmark has repeated runs; 1026 scored records are not 1026 independent questions. Existing grader behavior and expected states were not changed. Results were regraded offline after the reporting-alias export.

Model weights and their distribution license have not been published as part of this submission.
