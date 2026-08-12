#!/usr/bin/env bash
# Run a single experiment on a given physical GPU.
# Usage: PYTHON=<python_bin> scripts/run_exp.sh <gpu_index> <config_path>
set -e

GPU="$1"
CFG="$2"
NAME="$(basename "$CFG" .yaml)"
mkdir -p logs
PYBIN="${PYTHON:-python}"
echo "[run_exp] GPU=$GPU CFG=$CFG NAME=$NAME python=$PYBIN"
CUDA_VISIBLE_DEVICES="$GPU" "$PYBIN" train.py --config "$CFG" 2>&1 | tee "logs/train_${NAME}.log"
echo "[run_exp] DONE $NAME"
