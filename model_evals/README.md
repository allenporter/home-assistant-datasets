# Model Evaluation

## Pre-requisites

1. Create your virtual environment. If using a dev container just install the pip requirements.

    ```bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install --upgrade pip
    $ pip3 install -r requirements_dev.txt
    ```

The evaluations require custom components. You'll need to clone these and configure
them for use.

1. Configure any needed custom components under evaluation. You will need to clone somewhere https://github.com/allenporter/home-assistant-synthetic-home if using the evaluations in this package. If you are only
evaluating AI agents from home assistant core you can just add `home-assistant-synthetic-home` to the path:

```bash
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/../home-assistant-synthetic-home/custom_components/:${PWD}/../home-assistant-synthetic-home/"
```

Here is another example that configures multiple custom components when using local AI outside of
the core components in Home Assistant.

```bash
$ mkdir custom_components
$ cd custom_components
$ ln -s ../../home-assistant-synthetic-home/custom_components/synthetic_home synthetic_home
$ ln -s ../../hass-openai-custom-conversation/custom_components/vicuna_conversation vicuna_conversation
$ ln -s ../../home-assistant-summary-agent/custom_components/summary_agent summary_agent
$ cd ..
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/custom_components/"
```

## Model Config

Models are configured via config entries which are dynamically built from a
shorthand yaml configuration file which may contain urls or secrets to call
your model either in the cloud or local. This allows you to run the same set of
tasks across many models with minimal changes to the test configuration.

Create a `models.yaml` file in the root of this project has this format. This
file is not checked into git and is private to you.

```yaml
models:
#
# Cloud model examples
#
- model_id: gpt-4o
  domain: openai_conversation
  config_entry_data:
    api_key: sk-XXXXXXXXXXXXXXXXXXXXXXXX
    chat_model: gpt-4o
  config_entry_options:
    llm_hass_api: assist

- model_id: gemini-1.5-flash
  domain: google_generative_ai_conversation
  config_entry_data:
    api_key: XXXXXXXXXXXXXXXXXXXXXXXX
  config_entry_options:
    chat_model: models/gemini-1.5-flash-latest
    llm_hass_api: assist

# Example using a custom component
- model_id: mistral-7b-instruct
  domain: vicuna_conversation
  config_entry_data:
    api_key: sk-0000000000000000000
    base_url: http://llama-cublas.llama:8000/v1
  config_entry_options:
    llm_hass_api: assist

#
# Ollama examples
#

- model_id: llama3
  domain: ollama
  config_entry_data:
    url: https://ollama.example/"
    model: "llama3:latest"

- model_id: gemma
  domain: ollama
  config_entry_data:
    url: https://ollama.k8s.mrv.thebends.org/"
    model: "gemma:7b"
```


You can configure which models are in scope by changing the test fixtures.

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

## Synthetic Home Config

Most evaluations start up a synthetic home to use when testing. You can configure
which homes to test with a fixture.

```python
@pytest.fixture(
    name="synthetic_home_config",
    params=[
        "datasets/devices/dom1-pl.yaml",
        "datasets/devices/home1-us.yaml",
        "datasets/devices/home7-dk.yaml",
    ],
)
def synthetic_home_config_fixture(request: pytest.FixtureRequest) -> str:
    """Fiture that defines the synthetic home configuration to use."""
    return request.param
```

## Eval Design

The actual eval itself is a pytest test. Most evaluations use the following fixtures or data types:

- A task is typically a `@dataclass` that defines the unit of work to do.
- `tasks_provider`: Creates the actual parameters to use during the evaluation. This may
  read content from a yaml file and populate the task dataclass. For example,
  it may contain a set of devices, their state, and a conversation agent command.
- `prepare_state_fixture`: Sets the synthethic home device state as needed by the task
- `eval_record_writer`: Records the output of the conversation agent and any additioanl context
  needed to perform an evaluation (either offline or by human).
- A test: Consumes tasks from the task provider, sets the state with the state fixture,
  and calls the conversation agent.

## Running Data Collection

You can run the model evaluation to collect convesation agent outputs like this. **Note** that this will be making expensive
LLM calls.

```shell
py.test evals/test_device_actions_eval.py
```
