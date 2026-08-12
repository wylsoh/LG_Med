#!/usr/bin/env bash
# Launch an experiment in a DETACHED tmux session (survives server disconnects).
# Usage: PYTHON=<python_bin> scripts/tmux_run.sh <gpu_index> <config_path>
set -e

GPU="$1"
CFG="$2"
NAME="$(basename "$CFG" .yaml)"
SESSION="exp_${NAME}"
PYBIN="${PYTHON:-python}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "[tmux_run] session '$SESSION' exists -> kill & recreate"
    tmux kill-session -t "$SESSION"
fi

mkdir -p "$ROOT/logs"
tmux new-session -d -s "$SESSION" -c "$ROOT" \
    "CUDA_VISIBLE_DEVICES=$GPU '$PYBIN' train.py --config '$CFG' 2>&1 | tee '$ROOT/logs/train_${NAME}.log'; echo '[run] DONE $NAME'; sleep 2"
echo "[tmux_run] launched session '$SESSION' on GPU $GPU (name=$NAME)"
tmux ls
