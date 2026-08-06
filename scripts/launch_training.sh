#!/usr/bin/env bash
# Launch an SB3 training run fully detached from the calling shell, and open a
# separate GNOME Terminal window that tails its console log.
#
#   scripts/launch_training.sh <config.yaml> <tag> [extra train.py args...]
#
# The training process is started with `setsid nohup`, so it survives both the
# calling shell (e.g. a Claude Code session) and the tail window being closed.
# The tail window is only a viewer: closing it never stops training.
#
# Writes:
#   runs/<experiment_name>/console_<tag>.log   console output (stdout+stderr)
#   runs/<experiment_name>/<tag>.pid           PID of the training process
#
# Stop a run with: kill "$(cat runs/<experiment_name>/<tag>.pid)"

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$HOME/anaconda3/envs/horcrux/bin/python}"

if [[ $# -lt 2 ]]; then
    echo "usage: $(basename "$0") <config.yaml> <tag> [extra train.py args...]" >&2
    exit 2
fi

CONFIG="$1"
TAG="$2"
shift 2

[[ -f "$CONFIG" ]] || { echo "config not found: $CONFIG" >&2; exit 1; }
[[ -x "$PYTHON_BIN" ]] || { echo "python not found: $PYTHON_BIN" >&2; exit 1; }

# experiment.output_dir from the YAML decides where logs live.
OUTPUT_DIR="$("$PYTHON_BIN" - "$CONFIG" <<'PY'
import sys, yaml
cfg = yaml.safe_load(open(sys.argv[1]))
print(cfg["experiment"]["output_dir"])
PY
)"

LOG_DIR="$PROJECT_ROOT/$OUTPUT_DIR"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/console_${TAG}.log"
PID_FILE="$LOG_DIR/${TAG}.pid"

if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "a run tagged '$TAG' is already alive (pid $(cat "$PID_FILE"))" >&2
    exit 1
fi

cd "$PROJECT_ROOT"
setsid nohup "$PYTHON_BIN" training/train.py --config "$CONFIG" "$@" \
    >"$LOG_FILE" 2>&1 < /dev/null &
TRAIN_PID=$!
echo "$TRAIN_PID" > "$PID_FILE"

# Viewer window. Detached from this shell via setsid so it outlives the caller;
# gnome-terminal itself re-parents the window to gnome-terminal-server anyway.
if [[ -n "${DISPLAY:-}" ]] && command -v gnome-terminal >/dev/null; then
    setsid gnome-terminal \
        --title="train:${TAG} (pid ${TRAIN_PID})" \
        --geometry=118x36 \
        -- bash -c "printf '\033]0;train:${TAG} pid ${TRAIN_PID}\007';
                    echo '=== ${CONFIG} | pid ${TRAIN_PID} ===';
                    echo '=== ${LOG_FILE} ===';
                    echo '=== closing this window does NOT stop training ===';
                    echo;
                    tail -n 40 -f '${LOG_FILE}'" \
        >/dev/null 2>&1 < /dev/null &
    disown || true
else
    echo "warning: no DISPLAY or gnome-terminal; skipping viewer window" >&2
fi

echo "config : $CONFIG"
echo "pid    : $TRAIN_PID  (file: $PID_FILE)"
echo "log    : $LOG_FILE"
echo "tail   : tail -f $LOG_FILE"
