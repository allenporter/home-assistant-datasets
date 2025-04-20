# Evaluation dataset for Home Assistant assist actions

This is a dataset for the Home Assistant LLM API ([blog post](https://developers.home-assistant.io/blog/2024/05/20/llm-api/)).

Running an evaluation consists of two steps:

- Collecting data by scraping model outputs
- Evaluating the scraped outputs against the groundtruth results and summarizing metrics

The scraping and evaluation are implemented using `pytest` tests that write results
to local output files.

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

Models are configured in the `models/` file in the root of this repository. These
are configuration entries for home assistant integrations.

Here are example model configuration files:

```yaml
model_id: gemini-1.5-flash
domain: google_generative_ai_conversation
config_entry_data:
  api_key: XXXXXXXXXXXX
config_entry_options:
  chat_model: models/gemini-1.5-flash-latest
  llm_hass_api: assist
```

```yaml
model_id: gpt-4o
domain: openai_conversation
config_entry_data:
  api_key: sk-XXXXXXXXXXXX
config_entry_options:
  chat_model: gpt-4o
  llm_hass_api: assist
```

```yaml
model_id: llama3.1
domain: ollama
config_entry_data:
  url: !secret ollama_url
  model: llama3.1:latest
config_entry_options:
  llm_hass_api: assist
```

### Prepare environment

Create a virtual environment:

```bash
$ uv venv
$ source .venv/bin/activate
$ uv pip install -r requirements_dev.txt --prerelease=allow
$ uv pip install -r requirements_eval.txt
```

The above will by default use a somewhat recent version of home assistant but
if you want to use one from a local environment then install it:

```bash
$ pip3 install -e /workspaces/core
```

You will need the [synthetic-home custom component](https://github.com/allenporter/synthetic-home)
and you can either install it in a separate directory like this:

```bash
$ export PYTHONPATH="${PYTHONPATH}:/workspaces/home-assistant-synthetic-home/"
```

Or using a `custom_components` directory in the local directory if you have multiple
custom components you want to evaluate. This means you will need to sym link
all of the custom components into that directory:

```bash
$ export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

### Run

You can collect data from the API using the command, which uses pytest as the
underlying framework.

```bash
$ DATASET="datasets/assist/"
$ OUTPUT_DIR="reports/assist/2024.8.0b"  # Output based on home assistant version used
$ MODEL=llama3.1
$ pytest home_assistant_datasets/tool/assist/collect --models=${MODEL} --dataset=${DATASET} --model_output_dir=${OUTPUT_DIR}
```

If you don't know the homeassistant version, you can run `uv pip freeze | grep "^homeassistant=="` to find out.

## Evaluation

Once you have collected data from the model, you can automatically evaluate the results:

```bash
$ pytest home_assistant_datasets/tool/assist/eval --model_output_dir=${OUTPUT_DIR}
```

You can see the output reports created in `${OUTPUT_DIR}`.

See [Annotations](../../script/README.md) for details on how to systematically
run human annotations of the output. You can review the outputs manually if the
tasks do not support exhaustive scoring.
