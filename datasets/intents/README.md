# Evaluation dataset for Home Assistant intents

This is a dataset for the Home Assistant LLM API ([blog post](https://developers.home-assistant.io/blog/2024/05/20/llm-api/)) imported from the home assistant intents repo.

See the `home-assistant-datasets assist` command for more details on how to
run evaluations.

## Dataset details

This section contains information about the dataset. You can use the existing
definitions or define your own.

### Inventory

The evaluation will set up one synthetic home inventory file which is used to set
up the devices in the expected state and test out the conversation agent against it. You can
either use existing synthetic homes from the common datasets, or create your own
by hand. You may want to choose based on the device types to exercise.

The inventory should be placed in `_fixtures.yaml` in the dataset subdirectory.

A synthetic home is that it may include a broader set of devices in the house than
specifically whas is being tested in order to make it more realistic. This also helps
include distractors useful for evaluating the model such as additional devices not under test.

See [synthetic_home](https://github.com/allenporter/synthetic-home) for more about
an inventory definition or [home-assistant-synthetic-home](https://github.com/allenporter/home-assistant-synthetic-home)
for the custom component.

### Dataset Eval Tasks

See `home_assistant_datasets/tool/assist/data_model.py` for the definition of
the dataclasses that define the evaluation data. This includes the

The `data_model.py` file contains the dataclasses that hold data related to what
is being evaluated. e.g. information about words to say to the conversation agent,
relevant devices and their state used when testing.

#### Record

| Property               | Description                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------- |
| `category`             | A category used for slicing performance statistics                                  |
| `tests.sentences`      | A list of conversation inputs e.g. `Please turn on the light`                       |
| `tests.setup`          | Initial inventory entity state to setup in addition to the device fixture.          |
| `tests.expect_changes` | Differences in inventory entity states that are expected to change during the test. |
| `tests.ignore_changes` | Entity attributes (or keyword `state`) to ignore when calculating changes.          |

These dataclasses are populated based on yaml files in the dataset subdirectories.

## Data Collection

Now that the data collection tasks for the eval are defined, we want to decide
which parameters to adjust. This includes things like the model to use, the prompt, etc.

### Configure Conversation Agents

See the [model config](../README.md) section on how to configure `models.yaml`. Each
model name defines a config entry and the conversation agent to use during evaluation.

Here is an example `models.yaml`:

```yaml
models:
  - model_id: assistant
    domain: homeassistant

  - model_id: gemini-1.5-flash
    domain: google_generative_ai_conversation
    config_entry_data:
      api_key: XXXXXXXXXXXX
    config_entry_options:
      chat_model: models/gemini-1.5-flash-latest
      llm_hass_api: assist

  - model_id: gpt-4o
    domain: openai_conversation
    config_entry_data:
      api_key: sk-XXXXXXXXXXXX
    config_entry_options:
      chat_model: gpt-4o
      llm_hass_api: assist

  # Update when ollama supports tool calling
  - model_id: llama3.1
    domain: ollama
    config_entry_data:
      url: http://ollama.ollama:11434/
      model: llama3.1:latest
    config_entry_options:
      llm_hass_api: assist

  - model_id: mistral-7b-instruct
    domain: vicuna_conversation
    config_entry_data:
      api_key: sk-0000000000000000000
      base_url: http://llama-cublas.llama:8000/v1
    config_entry_options:
      llm_hass_api: assist
```

### Run

You can collect data from the API using the command, which uses pytest as the
underlying framework.

You need to have the synthetic home custom component installed with something like this:

```bash
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/../home-assistant-synthetic-home/"
```

Or otherwise configure custom components in the `custom_components` directory.

```bash
$ DATASET="home-assistant-datasets/datasets/assist/"
$ OUTPUT_DIR="reports/assist/$(date +"%Y-%m-%d")/"
$ home-assistant-datasets assist collect --models=assistant --dataset=${DATASET} --model_output_dir={OUTPUT_DIR}
```

See `home-assistant-datasets assist collect --help` for options to control pytest.

## Evaluation

Once you have collected data from the model, you can automatically evaluate the results:

```bash
$ home-assistant-datasets assist eval --model_output_dir=${OUTPUT_DIR} ${DATASET_DIR}
```
