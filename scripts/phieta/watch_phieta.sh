#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/phieta/watch_phieta.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"

PID_DIR=data/pids
LOG=""
PID=""

if [ -f "$PID_DIR/phieta.logpath" ]; then
  LOG=$(cat "$PID_DIR/phieta.logpath" 2>/dev/null || true)
fi
if [ -f "$PID_DIR/phieta.pid" ]; then
  PID=$(cat "$PID_DIR/phieta.pid" 2>/dev/null || true)
fi

if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
  echo "[phieta] running (PID=$PID)";
  [ -n "$LOG" ] && { echo "[phieta] log: $LOG"; echo "----- tail -n 40 -----"; tail -n 40 "$LOG" || true; }
  exit 0
fi

echo "[phieta] not running"
if [ -n "$LOG" ] && [ -f "$LOG" ]; then
  echo "[phieta] last log: $LOG"; echo "----- tail -n 60 -----"; tail -n 60 "$LOG" || true
fi
