#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/chain_after_ho_dirsig.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

HOLDOUT="${1:-AbellS1063}"
TRAIN="${2:-Abell1689,CL0024}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "[chain] Waiting for ho_dirsig batch to finish (if running)..." >&2
PID_FILE=$(ls -t tmp/jobs/ho_dirsig_knee_batch_*.pid 2>/dev/null | head -n1 || true)
if [ -n "$PID_FILE" ] && [ -s "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE" 2>/dev/null || echo 0)
else
  PID=$(pgrep -fo ".*make_bullet_holdout.py.*--band 8-16.*--perm-.*(6000|5000).*" || true)
fi
if [ -n "${PID:-}" ] && [ "$PID" -gt 0 ]; then
  echo "[chain] Detected running ho_dirsig PID=$PID; polling..." >&2
  while kill -0 "$PID" 2>/dev/null; do
    sleep 30
  done
  echo "[chain] ho_dirsig finished." >&2
else
  echo "[chain] No active ho_dirsig job detected; continuing." >&2
fi

echo "[chain] Dispatching A-3 knee grid for $HOLDOUT after ho_dirsig." >&2
scripts/jobs/batch_w_eff_knee.sh "$HOLDOUT" "$TRAIN"
echo "[chain] Done scheduling A-3 for $HOLDOUT." >&2

