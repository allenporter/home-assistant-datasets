#!/bin/bash
# This script is used to compute evaluation metrics on the assist dataset using
# pytest

DATASET_NAME=assist script/eval_metrics_assist.sh
DATASET_NAME=assist-mini script/eval_metrics_assist.sh
DATASET_NAME=questions script/eval_metrics_assist.sh

script/eval_metrics_automations.sh
