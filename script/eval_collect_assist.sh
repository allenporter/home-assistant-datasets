#!/bin/bash
# This script is used to evaluate the assist dataset using pytest.
# The arguments are:
#   - DATASET_NAME: The name of the dataset to evaluate (e.g., assist, assist-mini, questions).
#   - MODEL: The model to use for evaluation.

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

if [ -z "$MODEL" ]; then
  echo "MODEL is not set. Please set the MODEL environment variable."
  exit 1
fi
if [ ! -d "home_assistant_datasets" ]; then
    echo "home_assistant_datasets directory does not exist. Please run from repo root."
    exit 1
fi
if [ ! -d "${DATASET}" ]; then
  echo "Dataset directory ${DATASET} does not exist. Please check the dataset name."
  exit 1
fi
if [ ! -d "${OUTPUT_DIR}" ]; then
  echo "Output directory ${OUTPUT_DIR} does not exist. Creating it."
  mkdir -p "${OUTPUT_DIR}"
fi

# Ensure the synthetic home component is setup
SYNTHETIC_HOME_DIR="/workspaces/home-assistant-synthetic-home/"
if [ ! -d "${SYNTHETIC_HOME_DIR}" ]; then
  echo "Synthetic home directory ${SYNTHETIC_HOME_DIR} does not exist. Please check the path."
  exit 1
fi
export PYTHONPATH="${PYTHONPATH}:${SYNTHETIC_HOME_DIR}"

pytest home_assistant_datasets/tool/assist/collect --models=${MODEL} --dataset=${DATASET} --model_output_dir=${OUTPUT_DIR}
