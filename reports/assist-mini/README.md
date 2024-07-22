# Evaluation

This is an evaluation of Home Assistant 2024.8.0b (dev build) focused on the
`assist-mini` dataset which should be easier than `assist`. This is focused on
local models which have not performed that well on the `assist` dataset.

## Work log

### Pre-requisites

- Ensure any the synthetic home custom component is in the python environment e.g.:
  - `export PYTHONPATH="${PYTHONPATH}:/workspace/home-assistant-synthetic-home`
  - `export PYTHONPATH="${PYTHONPATH}:${PWD}"`
- Install this projects python dependencies e.g. `pip3 install -r requirements_dev.txt`

### Prepare Eval environment

Development version of home assistant

```bash
$ pip3 install -e /workspaces/core
$ DATASET="datasets/assist-mini/"
$ MODEL_OUTPUT_DIR="reports/assist-mini/2024.8.0b/"
```

### model setup

Using `models.yaml` to configure a local model integrations:

```yaml
- model_id: llama3-groq-tool-use
  domain: ollama
  config_entry_data:
    url: http://ml-papers-ollama.devpod/v1
    model: llama3-groq-tool-use:latest
  config_entry_options:
    llm_hass_api: assist
- model_id: mistral-v3
  domain: ollama
  config_entry_data:
    url: http://ml-papers-ollama.devpod/v1
    model: mistral-tools:latest
  config_entry_options:
    llm_hass_api: assist
```

### Collect data and run offline eval


```bash
$ MODEL=llama3-groq-tool-use
$ home-assistant-datasets assist collect --model_output_dir=${MODEL_OUTPUT_DIR} --dataset=${DATASET} --models=${MODEL}
$ home-assistant-datasets assist eval --model_output_dir=${MODEL_OUTPUT_DIR} --output_type=csv > ${MODEL_OUTPUT_DIR}/report.csv
```
