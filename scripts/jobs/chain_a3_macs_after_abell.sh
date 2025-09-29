#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/chain_a3_macs_after_abell.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "[chain2] Waiting for AbellS1063 A-3 (w_eff_knee) to run and finish..." >&2

find_pid() {
  pgrep -fo ".*scripts/reports/make_bullet_holdout.py.*--holdout AbellS1063.*BULLET_Q_KNEE|w_eff_knee_AbellS1063|batch_w_eff_knee.sh AbellS1063" || true
}

# Wait until AbellS1063 A-3 starts (either the batch script or the python runs)
for _ in $(seq 1 2400); do # up to ~20h with 30s sleep
  PID=$(find_pid)
  if [ -n "$PID" ]; then
    echo "[chain2] Detected AbellS1063 A-3 PID=$PID; waiting for completion..." >&2
    break
  fi
  sleep 30
done

if [ -n "${PID:-}" ]; then
  while kill -0 "$PID" 2>/dev/null; do
    sleep 30
  done
  echo "[chain2] AbellS1063 A-3 finished." >&2
else
  echo "[chain2] AbellS1063 A-3 was not detected; continuing anyway." >&2
fi

echo "[chain2] Dispatching A-3 knee grid for MACSJ0416." >&2
scripts/jobs/batch_w_eff_knee.sh MACSJ0416 Abell1689,CL0024
echo "[chain2] Done scheduling A-3 for MACSJ0416." >&2

