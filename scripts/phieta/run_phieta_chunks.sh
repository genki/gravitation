#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/phieta/run_phieta_chunks.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
# Chunked sweep runner to reduce memory usage; runs per-beta slices sequentially.
# Usage: scripts/phieta/run_phieta_chunks.sh NAMES="NGC3198" BETAS="0.0,0.3,0.6"

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

NAMES=${NAMES:-"NGC3198"}
BETAS=${BETAS:-"0.0,0.3,0.6"}
# Optional knobs: QUICK=1 to pass --quick, MAX_SIZE=192 to cap image size
EXTRA_ARGS=""
if [ "${QUICK:-}" = "1" ]; then
  EXTRA_ARGS+=" --quick"
fi
if [ -n "${MAX_SIZE:-}" ]; then
  EXTRA_ARGS+=" --max-size ${MAX_SIZE}"
fi
LOG_DIR=logs
PID_DIR=data/pids
mkdir -p "$LOG_DIR" "$PID_DIR"
TS=$(date -u +%Y%m%dT%H%M%SZ)
LOG_FILE="$LOG_DIR/phieta_chunks_${TS}.log"

if [ -f "$PID_DIR/phieta_chunks.pid" ] && kill -0 "$(cat $PID_DIR/phieta_chunks.pid)" 2>/dev/null; then
  echo "[phieta:chunks] already running (PID=$(cat $PID_DIR/phieta_chunks.pid))" >&2
  exit 0
fi

(
  set -x
  IFS=',' read -ra BS <<< "$BETAS"
  for b in "${BS[@]}"; do
    echo "[phieta:chunks] beta=$b" | tee -a "$LOG_FILE"
    PYTHONPATH=. ./.venv/bin/python scripts/reports/sweep_phieta_fair.py --names "$NAMES" --beta "$b" ${EXTRA_ARGS} || true
  done
  PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true
) >> "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_DIR/phieta_chunks.pid"
echo "$LOG_FILE" > "$PID_DIR/phieta_chunks.logpath"
echo "[phieta:chunks] pid=$PID log=$LOG_FILE"
