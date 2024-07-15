# Evaluation

This is an evaluation of Home Assistant 2024.7.0b focused on tool control LLMs.

## Work log

### Pre-requisites

- Ensure any the synthetic home custom component is in the python environment e.g. `export PYTHONPATH="${PYTHONPATH}:/workspace/home-assistant-synthetic-home`
- Install this projects python dependencies e.g. `pip3 install -r requirements_dev.txt`

### Prepare Eval environment

```bash
$ pip3 install homeassistant==2024.7.0
$ DATASET="./datasets/assist/"
$ MODEL_OUTPUT_DIR=reports/assist/2024.7.0/
```

### model setup

Using `models.yaml` to configure a local openai compatible integration:

```yaml
- model_id: functionary-7b-v1.4
  domain: vicuna_conversation
  config_entry_data:
    api_key: sk-0000000000000000000
    base_url: http://llama-cublas.llama:8000/v1
  config_entry_options:
    chat_model: functionary-7b-v1.4
    llm_hass_api: assist
```

### Assist pipeline baseline


```bash
$ MODEL=functionary-small-v2.5
$ home-assistant-datasets assist collect --model_output_dir=${MODEL_OUTPUT_DIR} --dataset=${DATASET} --models=${MODEL}
$ home-assistant-datasets assist eval --model_output_dir=${MODEL_OUTPUT_DIR} --output_type=csv > ${MODEL_OUTPUT_DIR}/report.csv
```

## Costs

The current evaluation with around 220 tasks has the following costs:
- An evaluation of gemini-flash-1.5 was free (though there may be geo restrictions)
- An evaluation of gpt-3.5 costed around $1.50
- An evaluation of gpt-4o costed around $4. You will also likely see heavy rate limiting, making it *very* slow.
