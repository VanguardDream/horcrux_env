#!/usr/bin/env bash
# Train the GD control group (direct torque) forward policy as one detached
# 5-stage pipeline, mirroring the gait-decomposition forward lineage in
# policies/path_tracking/forward (stages 01..05) for a fair ablation:
#
#   stage 1  from scratch          lr 3e-4, 5 epochs,            +7,864,320
#   stage 2  resume stage1 BEST    lr 1e-4, 3 epochs,            +100,000
#   stage 3  resume stage2 final   lr 1e-4, 3 epochs,            +7,864,320
#   stage 4  resume stage3 final   lr 5e-5, 2 epochs, kl 0.04,   +1,048,576
#   stage 5  resume stage4 final   lr 5e-5, 2 epochs, kl 0.04,   +30,720,000
#
#   scripts/run_dt_forward_pipeline.sh          # launch detached, prints pid/log
#   scripts/run_dt_forward_pipeline.sh --stages # internal: run stages in-process
#
# The detached worker survives the calling shell. Stop the whole pipeline with:
#   kill -- -"$(cat runs/ppo_plane_dt_forward_pipeline/pipeline.pid)"
# (negative pid kills the process group, including a running train.py)
#
# Writes:
#   runs/ppo_plane_dt_forward_pipeline/console_pipeline.log
#   runs/ppo_plane_dt_forward_pipeline/pipeline.pid
#   runs/ppo_plane_dt_forward_stage{1..5}/<timestamp>_.../   per-stage runs

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$HOME/anaconda3/envs/horcrux/bin/python}"
CFG_DIR="$PROJECT_ROOT/training/configs"
PIPE_DIR="$PROJECT_ROOT/runs/ppo_plane_dt_forward_pipeline"
LOG_FILE="$PIPE_DIR/console_pipeline.log"
PID_FILE="$PIPE_DIR/pipeline.pid"

if [[ "${1:-}" != "--stages" ]]; then
    [[ -x "$PYTHON_BIN" ]] || { echo "python not found: $PYTHON_BIN" >&2; exit 1; }
    for n in 1 2 3 4 5; do
        [[ -f "$CFG_DIR/ppo_plane_dt_forward_stage${n}.yaml" ]] || {
            echo "missing config: ppo_plane_dt_forward_stage${n}.yaml" >&2; exit 1; }
    done
    mkdir -p "$PIPE_DIR"
    if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo "pipeline already alive (pid $(cat "$PID_FILE"))" >&2
        exit 1
    fi
    setsid nohup bash "$0" --stages >"$LOG_FILE" 2>&1 < /dev/null &
    echo "$!" > "$PID_FILE"
    echo "pipeline pid : $(cat "$PID_FILE")  (file: $PID_FILE)"
    echo "log          : $LOG_FILE"
    echo "tail         : tail -f $LOG_FILE"
    exit 0
fi

# ---------------------------------------------------------------- stage worker
cd "$PROJECT_ROOT"

RUN_DIR=""
run_stage() {
    local config="$1" output_dir="$2"
    shift 2
    echo
    echo "==== [$(date '+%F %T')] START $(basename "$config") $* ===="
    "$PYTHON_BIN" training/train.py --config "$config" "$@"
    RUN_DIR="$(ls -td "$PROJECT_ROOT/$output_dir"/*/ 2>/dev/null | head -1)"
    RUN_DIR="${RUN_DIR%/}"
    if [[ -z "$RUN_DIR" || ! -f "$RUN_DIR/final_model.zip" ]]; then
        echo "==== STAGE FAILED: no final_model.zip under $output_dir ====" >&2
        exit 1
    fi
    echo "==== [$(date '+%F %T')] DONE  -> $RUN_DIR ===="
}

run_stage "$CFG_DIR/ppo_plane_dt_forward_stage1.yaml" runs/ppo_plane_dt_forward_stage1
S1="$RUN_DIR"
# The treatment group continued from stage 01's evaluation BEST, not final.
if [[ ! -f "$S1/evaluation/best_model.zip" ]]; then
    echo "==== STAGE FAILED: $S1/evaluation/best_model.zip missing ====" >&2
    exit 1
fi

run_stage "$CFG_DIR/ppo_plane_dt_forward_stage2.yaml" runs/ppo_plane_dt_forward_stage2 \
    --resume-model "$S1/evaluation/best_model.zip" \
    --resume-vecnormalize "$S1/evaluation/best_model_vecnormalize.pkl"
S2="$RUN_DIR"

run_stage "$CFG_DIR/ppo_plane_dt_forward_stage3.yaml" runs/ppo_plane_dt_forward_stage3 \
    --resume-model "$S2/final_model.zip" \
    --resume-vecnormalize "$S2/vecnormalize.pkl"
S3="$RUN_DIR"

run_stage "$CFG_DIR/ppo_plane_dt_forward_stage4.yaml" runs/ppo_plane_dt_forward_stage4 \
    --resume-model "$S3/final_model.zip" \
    --resume-vecnormalize "$S3/vecnormalize.pkl"
S4="$RUN_DIR"

run_stage "$CFG_DIR/ppo_plane_dt_forward_stage5.yaml" runs/ppo_plane_dt_forward_stage5 \
    --resume-model "$S4/final_model.zip" \
    --resume-vecnormalize "$S4/vecnormalize.pkl"
S5="$RUN_DIR"

echo
echo "==== [$(date '+%F %T')] PIPELINE COMPLETE ===="
echo "stage1: $S1"
echo "stage2: $S2"
echo "stage3: $S3"
echo "stage4: $S4"
echo "stage5: $S5"
