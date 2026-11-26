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
if [ -d "custom_components/synthetic_home" ]; then
  # If local custom_components setup exists, pytest.ini will load it automatically
  echo "==> Using local custom_components/synthetic_home"
elif [ -d "/workspaces/home-assistant-synthetic-home/" ]; then
  echo "==> Using legacy Codespace synthetic home component"
  export PYTHONPATH="${PYTHONPATH}:/workspaces/home-assistant-synthetic-home/"
elif [ -d "deps/home-assistant-synthetic-home/" ]; then
  echo "==> Using deps/home-assistant-synthetic-home/"
  export PYTHONPATH="${PYTHONPATH}:${PWD}/deps/home-assistant-synthetic-home/"
else
  echo "Synthetic home directory not found. Please run ./script/bootstrap first."
  exit 1
fi

pytest ${DATASET} --model_output_dir=${OUTPUT_DIR}
