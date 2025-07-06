#!/bin/bash
# This script is used to evaluate the assist dataset using pytest.
# The arguments are:
#   - MODEL: The model to use for evaluation.

if [ -z "$MODEL" ]; then
  echo "MODEL is not set. Please set the MODEL environment variable."
  exit 1
fi

DATASET_NAME=assist script/eval_collect_assist.sh
DATASET_NAME=assist-mini script/eval_collect_assist.sh
DATASET_NAME=questions script/eval_collect_assist.sh

script/eval_collect_automations.sh
