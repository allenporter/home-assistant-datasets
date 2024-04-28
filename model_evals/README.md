# Model Evaluation

## Pre-requisites

1. Create the virtual environment

    ```bash
    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install --upgrade pip
    $ pip3 install -r requirements.txt
    ```

The evaluations require custom components. You'll need to clone these and configure
them for use.

1. Configure any needed custom components under evaluation

```bash
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/../home-assistant-synthetic-home/custom_components/:${PWD}/../home-assistant-synthetic-home/"
```

Here is another example that configures multiple custom components for local AI:

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

The `models.yaml` file in the root of this project has this format:

```yaml
models:
#
# Cloud model examples
#
- model_id: gpt-3.5
  domain: openai_conversation
  config_entry_data:
    api_key: sk-XXXXXXXXXXXXXXXXXXXXXXXX

- model_id: gemini-pro
  domain: google_generative_ai_conversation
  config_entry_data:
    api_key: XXXXXXXXXXXXXXXXXXXXXXXX

# Example using a custom component
- model_id: mistral-7b-instruct
  domain: vicuna_conversation
  config_entry_data:
    api_key: sk-0000000000000000000
    base_url: http://llama-cublas.llama:8000/v1

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
        "gemini-pro",
        "gpt-3.5",
        "mistral-7b-instruct",
    ],
)
def model_id_fixture(request: pytest.FixtureRequest) -> str:
    """Fiture that defines which model is being evaluated."""
    return request.param
```

## Synthetic Home Config

```python
@pytest.mark.parametrize(
    ("synthetic_home_config"),
    [
        ("datasets/devices/home1-us.yaml"),
        ("datasets/devices/apartament4-pl.yaml"),
        ("datasets/devices/casa-adosada-en-la-costa-es.yaml"),
        ("datasets/devices/lakeside-retreat-de.yaml"),
    ],
)
async def test_collect_area_summaries(
```

## Configure secrets

The configuration entries can reference secrets outside of the code, so
you can stick them in `secrets.yaml` which is in the `.gitignore`:

```yaml
openai_api_key: sk-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
google_api_key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
vicuna_convesation_base_url: http://llama-cublas.llama:8000/v1
```

## Running the eval

You can run the evaluation like this. **Note** that this will be making expensive
LLM calls.

```shell
py.test evals/test_area_summary_eval.py
```
