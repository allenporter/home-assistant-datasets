# Device Actions

This folder contains an evaluation for a conversation agent acting on devices from
conversation commands. See the [model_evals README](../README.md)
for an overview of how evaluations work and setting up your environment. This
folder is meant to be more self contained than, with everything needed to do
the eval in this single directory.

## Preparing Synthetic Home(s)

The evaluation will set up one synthetic home which is used to set up the devices
in the expected state and test out the conversation agent against it. You can
either use existing synthetic homes from the common datasets, or create your own
by hand. You may want to choose based on the device types to exercise.

The main reason to pick a synthetic home is that it may include a broader set of
devices in the house that is more realistic and may contain distractors useful
for evaluating the model such as additional devices not under test.

This eval expects the synthetic homes to live in `model_evals/device_actions/dataset/`
so we've copied them there:

```
$ cp datasets/devices-v2/home7-dk.yaml model_evals/device_actions/dataset/
```

## Preparing Eval Tasks

The `data_model.py` file contains the dataclasses that hold data related to what
is being evaluated. e.g. information about words to say to the conversation agent,
relevant devices and their state used when testing.

### DeviceActionTask

| Property        | Description                                                     |
| --------------- | --------------------------------------------------------------- |
| `home_id`       | An identifier of the synthetic home to setup e.g. `home-us-1`   |
| `input_text`    | Conversation input e.g. `Please turn on the light`              |
| `device_states` | One or more initial device states used when preparing the home. |

These dataclasses are populated based on yaml files in the `dataset/` directory
that are populated form synthetic data or by hand.

A `DeviceState` contains a device `name` (e.g. _Kitchen Light_), it's `area` (e.g. _Kitchen_)
and the `state` (e.g. _on_) to set at the start of the test.

The device states supported by default are defined in [synthetic_home](https://github.com/allenporter/synthetic-home) in the [registry](https://github.com/allenporter/synthetic-home/tree/main/synthetic_home/registry) or they can be extended by adding more device types to the synthetic home config.

## Configure Data Collection

Now that the data collection tasks for the eval are defined, we want to decide
which parameters to adjust. This includes things like the model to use, the prompt,
or manually adjusting which data collection tasks are in scope.

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
    chat_model: gpt-4o
  config_entry_options:
    llm_hass_api: assist

# Update when ollama supports tool calling
- model_id: llama3
  domain: ollama
  config_entry_data:
    url: http://ollama.ollama:11434/
    model: llama3:latest

- model_id: mistral-7b-instruct
  domain: vicuna_conversation
  config_entry_data:
    api_key: sk-0000000000000000000
    base_url: http://llama-cublas.llama:8000/v1
  config_entry_options:
    llm_hass_api: assist
```

```python
@pytest.fixture(
    name="model_id",
    params=[
        "gemini-1.5-flash",
        "gpt-4o",
        "mistral-7b-instruct",
    ],
)
def model_id_fixture(request: pytest.FixtureRequest) -> str:
    """Fiture that defines which model is being evaluated."""
    return request.param
```

### Configure eval tasks

By default this will read all tasks in the `dataset/` directory but you can configure
to read a single task instead e.g. `model_evals/device_actions/dataset/dom1-pl.yaml` for testing.

```python
@pytest.fixture(
    name="record_filename",
    params=[(filename) for filename in dataset_files()],
    ids=[str(filename) for filename in dataset_files()],
)
def record_filename_fixture(request: pytest.FixtureRequest) -> str:
    """Fixture that reads the records from the dataset."""
    return request.param
```

## Configure Output

The outputs are stored based on the model under evaluation, but can be updated
to include other variables (e.g. if you are comparing different prompts, etc)

```python
@pytest.fixture(name="eval_output_file")
def eval_output_file_fixture(model_id: str, record_filename: str) -> str:
    """Sets the output filename for the evaluation run."""
    return pathlib.Path(f"{DIR}/output/{model_id}/{record_filename.name}.yaml")
```

## Run data collection

You can now run the input phrases against the configured conversation agent.

```bash
$ py.test model_evals/device_actions/test_device_actions_eval.py
```

If you want to iterate on a subset of the evaluation:

```bash
$ py.test model_evals/device_actions/test_device_actions_eval.py --collect-only
...
        <Coroutine test_collect_device_actions[model_evals/device_actions/dataset/home5-cn-fan.yaml-assistant]>
...
```

Then you can run a single eval like this with debug enabled

```bash
$ py.test 'model_evals/device_actions/test_device_actions_eval.py::test_collect_device_actions[model_evals/device_actions/dataset/dom1-pl-todo-list.yaml-assistant]' -s -vv
```

## Evaluate

See [Annotations](../../script/README.md) for details on how to systematically
run human annotations of the output. You can review the outputs manually without
scoring exhaustively.
