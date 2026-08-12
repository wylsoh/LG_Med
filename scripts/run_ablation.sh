#!/usr/bin/env bash
# Launch the front-end text-ablation experiments (E1-E5) in parallel.
# Each experiment is a separate process pinned to one physical GPU.
# Adjust the GPU mapping according to what is free (nvidia-smi).
set -e
cd "$(dirname "$0")/.."

# mode : gpu  (assign experiments to free GPUs)
declare -a MODES=(full location nature quantity keyword)
declare -a GPUS=(0 3 1 2 0)

PIDS=()
for i in "${!MODES[@]}"; do
    m="${MODES[$i]}"; g="${GPUS[$i]}"
    echo "[launch] $m on GPU $g"
    scripts/run_exp.sh "$g" "config/exp/${m}.yaml" &
    PIDS+=($!)
done

echo "Launched ${#PIDS[@]} experiments. Waiting..."
for p in "${PIDS[@]}"; do
    wait "$p"
done
echo "ALL ABLATION EXPERIMENTS DONE"
