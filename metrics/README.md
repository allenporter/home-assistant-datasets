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
leaderboard:
  mistral-7b-instruct-10-shot: 91.1%
  llama3-10-shot: 87.8%
  llama3-zero-shot: 87.8%
  gpt-3.5-zero-shot: 87.8%
  mistral-7b-instruct-zero-shot: 84.4%
  gemma-zero-shot: 83.3%
  gpt-3.5-10-shot: 80.0%
  gemma-5-shot: 77.8%
  gemma-3-shot: 76.7%
  gemma-10-shot: 53.3%
hardest_tasks:
- The hallway motion sensor is triggered, indicating movement. (0.0)
- The hallway light is on and the motion sensor is triggered. (0.0)
- The hallway lights are off, and the hallway motion sensor has not detected any movement
  for the past hour. (0.0)
- The garage door has been open for 12 minutes. (0.0)
- The hallway lights are on and the motion sensor has detected motion. (11.11111111111111)
```
