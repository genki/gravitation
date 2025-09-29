#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/phieta/run_phieta_bg.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
# Backgound runner for fair Phi·eta comparison+sweep with progress logging.
# Usage: scripts/phieta/run_phieta_bg.sh [NAMES="NGC3198,NGC2403"]

ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

NAMES=${NAMES:-"NGC3198,NGC2403"}
LOG_DIR=logs
PID_DIR=data/pids
mkdir -p "$LOG_DIR" "$PID_DIR"
TS=$(date -u +%Y%m%dT%H%M%SZ)
LOG_FILE="$LOG_DIR/phieta_${TS}.log"

if [ -f "$PID_DIR/phieta.pid" ] && kill -0 "$(cat $PID_DIR/phieta.pid)" 2>/dev/null; then
  echo "[phieta] already running (PID=$(cat $PID_DIR/phieta.pid))" >&2
  exit 0
fi

echo "[phieta] starting fair compare+sweep for: $NAMES" | tee -a "$LOG_FILE"

(
  set -x
  PYTHONPATH=. ./.venv/bin/python scripts/reports/compare_ws_vs_phieta.py --names "$NAMES"
  PYTHONPATH=. ./.venv/bin/python scripts/reports/sweep_phieta_fair.py --names "$NAMES"
  PYTHONPATH=. ./.venv/bin/python scripts/build_state_of_the_art.py || true
) >> "$LOG_FILE" 2>&1 &

PID=$!
echo $PID > "$PID_DIR/phieta.pid"
echo "$LOG_FILE" > "$PID_DIR/phieta.logpath"
echo "[phieta] pid=$PID log=$LOG_FILE"
