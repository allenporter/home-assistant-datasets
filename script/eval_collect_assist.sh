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

pytest home_assistant_datasets/tool/assist/collect --models=${MODEL} --dataset=${DATASET} --model_output_dir=${OUTPUT_DIR}
