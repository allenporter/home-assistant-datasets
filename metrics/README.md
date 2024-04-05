# Metrics

Compute metrics of the human annotated dataset.

Here is an example of dumping the aggregate stats of doccano ratings by model:

```yaml
$ python3 metrics/metrics.py --model_outputs model_outputs/area_summary/
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
