#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/phieta/cancel_phieta.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT_DIR"
PID_FILE=data/pids/phieta.pid
if [ ! -f "$PID_FILE" ]; then
  echo "[phieta] no pid file" >&2; exit 0
fi
PID=$(cat "$PID_FILE" 2>/dev/null || true)
if [ -z "$PID" ]; then
  echo "[phieta] empty pid" >&2; exit 0
fi
if kill -0 "$PID" 2>/dev/null; then
  echo "[phieta] sending SIGTERM to $PID"; kill "$PID" || true
  sleep 1
fi
if kill -0 "$PID" 2>/dev/null; then
  echo "[phieta] still running; sending SIGKILL"; kill -9 "$PID" || true
fi
echo "[phieta] cancelled"
