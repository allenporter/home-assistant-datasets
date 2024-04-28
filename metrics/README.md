# Metrics

Compute metrics of annotated datasets.

##  Human annotated dataset.

Here is an example of dumping the aggregate stats of doccano ratings by model:

```yaml
$ python3 metrics/human_eval_metrics.py --model_outputs model_outputs/area_summary/
---
gemini-pro:
  Bad: 7
  Good: 46
  Neutral: 7
gpt-3.5:
  Bad: 3
  Good: 55
  Neutral: 2
mistral-7b-instruct:
  Bad: 29
  Good: 22
  Neutral: 9
```


## Offline Evaluation

This is an example of computing an offline evaluation from a labeled dataset:

```bash
$ python3 metrics/offline_eval_metrics.py --model_outputs=model_outputs/anomaly/
---
gemma-10-shot: 51.1%
gemma-zero-shot: 85.6%
gpt-3.5-10-shot: 80.0%
gpt-3.5-zero-shot: 87.8%
llama3-10-shot: 87.8%
llama3-zero-shot: 87.8%
mistral-7b-instruct-10-shot: 91.1%
mistral-7b-instruct-zero-shot: 84.4%
```
