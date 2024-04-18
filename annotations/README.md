## Human Anotations

Humans can annotate the results (e.g. great, ok, bad)

## Doccano

See https://doccano.github.io/doccano/ for installation.

1. Create a new project e.g. `Area Summary`
1. Create the tags e.g. `Good`, `Bad`, `Neutral`.
1. We want these options for the project:
  - Allow single label.
  - Randomize Document order
  - Share annotations across users

## Import dataset

We want the data in the following format for doccano:

```json
[
    {
        "context": "Terrible customer service.",
        "response": ["negative"]
    },
    {
        "context": "Really great transaction.",
        "response": ["positive"]
    },
    ...
]
```

Here is an example of how to convert an unlabeled dataset for import into doccano. This
creates a single input file from all model outputs merged together. The results
are randomized in doccano and can be rated blind:

```bash
cat model_outputs/area_summary/*/*.yaml  | python annotations/import.py > model_outputs/area_summary/dataset.json
```

Create labels of `Good`, `Bad`, and `Neutral` and export the dataset when done labeling.

## Export Ratings

Convert the labeled JSONL output into yaml.

```bash
$ cat model_outputs/area_summary_agent/annotations.jsonl  | python annotations/export.py  > model_outputs/area_summary_agent/annotations.yaml
```

The output file contains the labeled task results which can be joined with the original
model output and used for computing metrics:

```yaml
---
uuid: e0fee440-e99d-4ecf-8dc9-8f686e51db3e
task_id: apartament4-bedroom-1-bedroom-1-light-on
label:
- Good

---
uuid: c28639af-7184-42c6-a0e5-7de453e8413e
task_id: apartament4-bedroom-1-bedroom-1-light-off
label:
- Neutral
```
