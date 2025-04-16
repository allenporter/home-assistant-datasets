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

Below is an example of scraping solutions from a model defined in `models/`.
Note that a model may be defined in terms of any conversatio agent, including
custom components.

```
$ DATASET_DIR=datasets/automations/
$ MODELS=gemini-1.5-flash
$ OUTPUT_DIR=reports/automations/2025.3.0b
$ home-assistant-datasets automation collect --models=${MODELS} --model_output_dir=${OUTPUT_DIR} --dataset=${DATASET_DIR} --count=5
```

## Evaluate

Now that the model has generated output, you can run them against the solution
test cases. In the future you will be able to validate solutions like this:

```
$ home-assistant-datasets automation eval --model_output_dir=${OUTPUT_DIR} ${DATASET_DIR}
```

## Creating new Problems

You may create a new problem in the benchmark by writing a description, writing a solution
and test for it, then hooking it into the eval system.

1. Write a `DESCRIPTION.md` that describes the high level problem, documents required inputs,
   and gives some example use cases.
2. Create a yaml file for the eval task, e.g. like `light_on_door/light_on_door.yaml`. This yaml file describes the problem by including the `DESCRIPTION.md` as a sentence,
3. Create the `_fixtures.yaml` either manually or with the `create-inventory` command above. You can pick an existing home to use from `devices-v3` and copy to `_home.yaml` to use as input.
4. Create the `solution.yaml` that takes the inputs described in `DESCRIPTION.md`.
5. Create an empty `__init__.py` to allow tests to run.
6. Verify the solution works with a `test_blueprint.py` running the eval command above under "Solutions".

You can then collect predictions from models as shown above for the problem.
TODO: We need to update the collect tool to allow scraping a single problem.
