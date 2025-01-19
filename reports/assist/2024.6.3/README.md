# Evaluation

This is an evaluation of Home Assistant 2024.6.3

## Work log

### Pre-requisites

- Ensure any the synthetic home custom component is in the python environment e.g. `export PYTHONPATH="${PYTHONPATH}:/workspace/home-assistant-synthetic-home`
- Install this projects python dependencies e.g. `pip3 install -r requirements_dev.txt && pip3 install -r requirements_eval.txt`

### Prepare Eval environment

```bash
$ pip3 install homeassistant==2024.6.3
$ MODEL_OUTPUT_DIR=reports/assist/2024.6.3/
$ DATASET="./datasets/assist/"
$ REPORT_DIR="./reports/assist/2024.6.3/"
```

Note that you can also reference a local home-assistant core repo with `pip3 -e install /workspace/core` or similar. You also need to configure the synthetic-home

### Assist pipeline baseline

Set a baseline with assistant of 50%:

```bash
$ home-assistant-datasets assist collect --model_output_dir=${MODEL_OUTPUT_DIR} --dataset=${DATASET} --models=assistant
$ home-assistant-datasets assist eval --model_output_dir=${MODEL_OUTPUT_DIR} --output_type=csv > ${REPORT_DIR}/report.csv
$ wc -l ${MODEL_OUTPUT_DIR}/report.csv
111 reports/assist/2024.6.3//report.csv
$ grep Good ${MODEL_OUTPUT_DIR}/report.csv | wc -l
56
$ python3 -c "print(56.0/111)"
0.5045045045045045
```

## Costs

The current evaluation with around 220 tasks has the following costs:
- An evaluation of gemini-flash-1.5 was free (though there may be geo restrictions)
- An evaluation of gpt-3.5 costed around $1.50
- An evaluation of gpt-4o costed around $4. You will also likely see heavy rate limiting, making it *very* slow.
