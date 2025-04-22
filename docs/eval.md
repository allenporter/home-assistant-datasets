# Evaluation

This is a quickstart with step by step instructions for how to run an evaluation
with an existing model and integration.

## Prepare environment

### Dependencies (required)

Create a virtual environment:

```bash
$ uv venv
$ source .venv/bin/activate
$ uv pip install -r requirements_dev.txt --prerelease=allow
$ uv pip install -r requirements_eval.txt --prerelease=allow
```

### Local Home Assistant (optional)

The above will by default use a somewhat recent version of home assistant but
if you want to use one from a local environment then install it:

```bash
$ uv pip install -e /workspaces/core
```

## Synthetic Home Custom Component (required)

You will need the [synthetic-home custom component](https://github.com/allenporter/home-assistant-synthetic-home)
and need to configure `PYTHONPATH` so that Home Assistant can find it. This is
typical setup for a custom component in a spearate directory:

```bash
$ git clone https://github.com/allenporter/home-assistant-synthetic-home
$ export PYTHONPATH="${PYTHONPATH}:/workspaces/home-assistant-synthetic-home/"
```

## Additional custom components (optional)

If you want to run additional custom components

Or using a `custom_components` directory in the local directory if you have multiple
custom components you want to evaluate. This means you will need to sym link
all of the custom components (including synthetic home) into that directory:

```bash
$ export PYTHONPATH="${PYTHONPATH}:${PWD}"
```

## Model setup

Models are configured in the `models/` directory with a file for each
model and integration combination. This may reference an integration in core
or a custom component you have installed locally.

An example `models/llama3.1.yaml` has a configuration file like this:

```yaml
model_id: llama3.1
domain: ollama
config_entry_data:
  url: !secret ollama_url
  model: llama3.1:latest
config_entry_options:
  llm_hass_api: assist
```

This includes referencing a secret defined in `secrets.yaml` in the root dir.

### Scape

You can scrape the model by running the `collect` command which will invoke
the onversation agent, using pytest. This loads the input `$DATASET`,
scrapes the model `$MODEL`, and the output to `$OUTPUT_DIR`.

Common datasets to evaluate against are `assist`, `assist-mini`, and `intents`.

```bash
$ DATASET="datasets/assist/"
$ MODEL=llama3.1
$ OUTPUT_DIR="reports/assist/2024.8.0b"  # Output based on home assistant version used
$ pytest home_assistant_datasets/tool/assist/collect --models=${MODEL} --dataset=${DATASET} --model_output_dir=${OUTPUT_DIR}
```

If you don't know the homeassistnat version, you can run `uv pip freeze | grep "^homeassistant=="` to find out.

### Evaluate

You then need to score the outputs by running the `eval` command. This report includes
a list of the wins and losses for manual inspection.

```bash
$ pytest home_assistant_datasets/tool/assist/eval --model_output_dir=${OUTPUT_DIR}
```

### Leaderboard

The leaderboard is generated from all of the model eval results checked into
the repo. You can update with these commands:

```bash
$ home-assistant-datasets leaderboard build
```

You can commit these and send a PR to update the official leaderboard.
