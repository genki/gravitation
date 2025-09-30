#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/chain_a4_after_full.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# Wait for an A-3 FULL job to finish, then dispatch A-4 FAST grid.
# Usage: chain_a4_after_full.sh HOLDOUT [TRAIN_CLUSTERS]

HOLDOUT="${1:-AbellS1063}"
TRAIN="${2:-Abell1689,CL0024}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# Find the latest FULL job pidfile for the holdout (either manual or auto_full_*)
PID_FILE=$(ls -t tmp/jobs/w_eff_knee_full_sel_${HOLDOUT}_*.pid 2>/dev/null | head -n1 || true)
if [ -z "$PID_FILE" ] || [ ! -s "$PID_FILE" ]; then
  PID_FILE=$(ls -t tmp/jobs/auto_full_${HOLDOUT}_*.pid 2>/dev/null | head -n1 || true)
fi

if [ -z "$PID_FILE" ] || [ ! -s "$PID_FILE" ]; then
  echo "[chain-a4] No FULL pidfile found for $HOLDOUT; exiting without dispatch." >&2
  exit 0
fi

PID=$(cat "$PID_FILE" 2>/dev/null || echo 0)
if [ -z "$PID" ] || [ "$PID" -le 0 ]; then
  echo "[chain-a4] Invalid PID in $PID_FILE; exiting." >&2
  exit 0
fi

echo "[chain-a4] Waiting for FULL PID=$PID to finish before running A-4 FAST ($HOLDOUT)." >&2
while kill -0 "$PID" 2>/dev/null; do
  sleep 30
done
echo "[chain-a4] FULL finished. Dispatching A-4 FAST grid for $HOLDOUT." >&2

scripts/jobs/dispatch_bg.sh -n "sepsf_grid_fast_${HOLDOUT}" --scope -- \
  "bash scripts/jobs/batch_se_psf_grid_fast.sh '$HOLDOUT' '$TRAIN'"

echo "[chain-a4] done" >&2

