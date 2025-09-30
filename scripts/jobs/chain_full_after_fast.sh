#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/chain_full_after_fast.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

HOLDOUT="${1:-MACSJ0416}"
TRAIN="${2:-Abell1689,CL0024}"
TOP_N="${3:-4}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

PID_FILE=$(ls -t tmp/jobs/run_knee_fast_${HOLDOUT}_*.pid 2>/dev/null | head -n1 || true)
if [ -z "$PID_FILE" ] || [ ! -s "$PID_FILE" ]; then
  echo "[chain-full] No FAST pidfile found for $HOLDOUT; exiting" >&2
  exit 0
fi
PID=$(cat "$PID_FILE" 2>/dev/null || echo 0)
if [ -z "$PID" ] || [ "$PID" -le 0 ]; then
  echo "[chain-full] Invalid PID; exiting" >&2
  exit 0
fi
echo "[chain-full] Waiting for FAST PID=$PID to finish..." >&2
while kill -0 "$PID" 2>/dev/null; do
  sleep 20
done
echo "[chain-full] FAST finished. Summarizing and dispatching FULL (TOP_N=$TOP_N)." >&2

# Summarize FAST runs and then auto-dispatch FULL
PYTHONPATH=. ./.venv/bin/python scripts/reports/summarize_knee_runs.py --holdout "$HOLDOUT" || true
scripts/jobs/dispatch_full_from_fast.sh "$HOLDOUT" "$TRAIN" "$TOP_N" || true
echo "[chain-full] done" >&2

