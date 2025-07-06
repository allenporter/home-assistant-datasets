#!/bin/bash
# This script is used to compute evaluation metrics on the assist dataset using
# pytest
# The arguments are:
#   - DATASET_NAME: The name of the dataset to evaluate (e.g., assist, assist-mini, questions).

set -e

if [ -z "$DATASET_NAME" ]; then
  echo "DATASET_NAME is not set. Please set the DATASET_NAME environment variable."
  exit 1
fi

DATASET="datasets/${DATASET_NAME}/"
if [ ! -d "$DATASET" ]; then
  echo "Dataset directory ${DATASET} not found. DATASET_NAME environment variable to a valid path."
  exit 1
fi

HA_VERSION=$(pip freeze | grep "^homeassistant==" | cut -f 3 -d '=')
OUTPUT_DIR="reports/${DATASET_NAME}/${HA_VERSION}"  # Output based on home assistant version used

if [ ! -d "${OUTPUT_DIR}" ]; then
  echo "Previous model run output directory ${OUTPUT_DIR} does not exist."
  exit 1
fi

pytest home_assistant_datasets/tool/assist/eval --model_output_dir=${OUTPUT_DIR}
cat ${OUTPUT_DIR}/reports.yaml
