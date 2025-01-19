# Evaluation

This is an evaluation of Home Assistant 2024.7.0b focused on tool control LLMs.

## Work log

### Pre-requisites

- Ensure any the synthetic home custom component is in the python environment e.g. `export PYTHONPATH="${PYTHONPATH}:/workspace/home-assistant-synthetic-home`
- Install this projects python dependencies e.g. `pip3 install -r requirements_dev.txt && pip3 install -r requirements_eval.txt`

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

### Collect data and run offline eval


```bash
$ MODEL=functionary-small-v2.5
$ home-assistant-datasets assist collect --model_output_dir=${MODEL_OUTPUT_DIR} --dataset=${DATASET} --models=${MODEL}
```

View the eval results for all models:
```bash
$ home-assistant-datasets assist eval --model_output_dir=${MODEL_OUTPUT_DIR} --output_type=report
```

Create a csv file of all the detailed results for review in a spreadsheet app like Google Sheets:
```bash
$ home-assistant-datasets assist eval --model_output_dir=${MODEL_OUTPUT_DIR} --output_type=csv > ${MODEL_OUTPUT_DIR}/report.csv
```
