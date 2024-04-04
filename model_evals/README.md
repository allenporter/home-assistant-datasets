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
$ ln -s ../../home-assistant-synthetic-home/custom_components/synthetic_home custom_components/synthetic_home
$ ln -s ../../hass-openai-custom-conversation/custom_components/vicuna_conversation custom_components/vicuna_conversation
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/custom_components/"
```

## Model Config

You can configure which models are in scope by changing the test fixtures.

```python
@pytest.fixture(
    name="model_config",
    params=[
        (ModelConfig("google_generative_ai_conversation", "gemini-pro")),
        (ModelConfig("openai_conversation", "gpt-3.5")),
        (ModelConfig("vicuna_conversation", "mistral-7b-instruct")),
    ],
)
def model_config_fixture(request: pytest.FixtureRequest) -> ModelConfig:
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
