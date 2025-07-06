#!/bin/bash
# This script is used to compute evaluation metrics on the assist dataset using
# pytest

set -e

DATASET_NAME="automations"
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

# Ensure the synthetic home component is setup
SYNTHETIC_HOME_DIR="/workspaces/home-assistant-synthetic-home/"
if [ ! -d "${SYNTHETIC_HOME_DIR}" ]; then
  echo "Synthetic home directory ${SYNTHETIC_HOME_DIR} does not exist. Please check the path."
  exit 1
fi
export PYTHONPATH="${PYTHONPATH}:${SYNTHETIC_HOME_DIR}"

pytest ${DATASET} --model_output_dir=${OUTPUT_DIR}
