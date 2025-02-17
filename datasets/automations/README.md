# Automation Dataset

## Overview

A dataset for evaluating automation generation. The homes for this dataset were
synthetically generated using gpt-3.5. This dataset is in development and contains
just a few initial examples. Each benchmark creates a synthetic home fixture
and configures the entities with a particular state, then asks for an automation
for a specific set of devices. The benchmark contains a event that should
trigger the automation, and an expected end state.

## Inventory creation

The `_home.yaml` is a synthetic home in the format defined by https://github.com/allenporter/synthetic-home
copied from one of the homes in `../devices-v3'.

The `_fixtures.yaml` is the actual inventory file format used by the evaluation.
You may update the inventory file from the home file with:

```
$ DATASET_DIR=datasets/automations/
$ synthetic-home create_inventory ${DATASET_DIR}/light_on_door/_home.yaml > ${DATASET_DIR}/light_on_door/_fixtures.yaml
```

## Solutions

You can run the baseline solutions in `datasets/automations/` against the test
harness. This runs the tests to ensure the existing solutions are correct.

```
$ DATASET_DIR=datasets/automations/
$ home-assistant-datasets automation eval ${DATASET_DIR}
```

## Scrape

See `/docs/eval.md` for details on how to setup the eval environment.

Below is an example of scraping solutions from a model defined in `models.yaml`.
Note that a model may be defined in terms of any conversatio agent, including
custom components.

```
$ DATASET_DIR=datasets/automations/
$ MODELS=gemini-1.5-flash
$ OUTPUT_DIR=reports/automations/2025.2.0b
$ home-assistant-datasets automation collect --models=${MODELS} --model_output_dir=${OUTPUT_DIR} --dataset=${DATASET_DIR}
```

## Evaluate

...
