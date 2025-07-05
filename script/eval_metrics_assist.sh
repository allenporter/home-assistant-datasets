#!/bin/bash
# This script is used to compute evaluation metrics on the assist dataset using
# pytest
# The arguments are:
#   - MODEL: The model to use for evaluation.

set -e

DATASET_NAME="assist"

HA_VERSION=$(pip freeze | grep "^homeassistant==" | cut -f 3 -d '=')
OUTPUT_DIR="reports/${DATASET_NAME}/${HA_VERSION}"  # Output based on home assistant version used

if [ ! -d "${OUTPUT_DIR}" ]; then
  echo "Previous model run output directory ${OUTPUT_DIR} does not exist."
  exit 1
fi

pytest home_assistant_datasets/tool/assist/eval --model_output_dir=${OUTPUT_DIR}
cat ${OUTPUT_DIR}/reports.yaml
