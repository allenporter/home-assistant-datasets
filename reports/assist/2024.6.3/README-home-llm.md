# Home LLM Evaluation

This is an evaluation of [Home LLM](https://github.com/acon96/home-llm) running home llm v3

## Work log

### Pre-requisites

- Configure Ollama with `fixt/home-3b-v3:latest` ([example](https://github.com/allenporter/k8s-gitops/commit/55a4b5a86a33d1ae43f7d62075a04507f19e68de))
- Make sym links in `custom_components` to `home-assistant-synthetic-home` and `home-llm` custom components.
- Ensure any the synthetic home custom component is in the python environment e.g. `export PYTHONPATH="${PYTHONPATH}:${PWD}`
- Install this python dependencies for all projects e.g. `pip3 install -r requirements_dev.txt && pip3 install -r requirements_eval.txt`

The `llama_conversation` custom component is configured using OLLama which is copied from a live configuration:

Here is an example `models.yaml` you need to configure the Home LLM custom component:

```yaml
models:
- model_id: assistant
  domain: homeassistant
- model_id: home-llm
  domain: llama_conversation
  version: 2
  config_entry_data:
    model_backend: ollama
    host: ollama.ollama
    port: "11434"
    ssl: false
    huggingface_model: fixt/home-3b-v3:latest
  config_entry_options:
    llm_hass_api: home-llm-service-api
    prompt: "You are 'Al', a helpful AI Assistant that controls the devices in a house. Complete the following task as instructed with the information provided only.\nThe current time and date is {{ (as_timestamp(now()) | timestamp_custom(\"%I:%M %p on %A %B %d, %Y\", \"\")) }}\nServices: {{ formatted_tools }}\nDevices:\n{{ formatted_devices }}"
    prompt_template: "zephyr"
    tool_format: "min_tool_format"
    tool_multi_turn_chat: false
    in_context_examples: false
    in_context_examples_file: "in_context_examples.csv"
    num_in_context_examples: 4.0
    max_new_tokens: 128
    context_length: 2048.0
    top_k: 40.0
    temperature: 0.1
    top_p: 1.0
    typical_p: 1.0
    ollama_json_mode: false
    request_timeout: 90.0
    ollama_keep_alive: 30.0
    remote_use_chat_endpoint: false
    extra_attributes_to_expose:
      - rgb_color
      - brightness
      - temperature
      - humidity
      - fan_mode
      - media_title
      - volume_level
      - item
      - wind_speed
    service_call_regex: "```homeassistant\\n([\\S \\t\\n]*?)```"
    refresh_prompt_per_turn: true
    remember_conversation: true
    remember_num_interactions: 5
```

### Prepare Eval environment

```bash
$ pip3 install homeassistant==2024.6.3
$ MODEL_OUTPUT_DIR=reports/assist/2024-06-30
$ DATASET="./datasets/assist/"
```

webcolors<=1.13

Note that you can also reference a local home-assistant core repo with `pip3 -e install /workspace/core` or similar. You also need to configure the synthetic-home

### Assist pipeline baseline

Set a baseline with assistant of 50%:

```bash
$ home-assistant-datasets assist collect --model_output_dir=${MODEL_OUTPUT_DIR} --dataset=${DATASET} --models=assistant
$ home-assistant-datasets assist eval --model_output_dir=${MODEL_OUTPUT_DIR} ${DATASET}
```
