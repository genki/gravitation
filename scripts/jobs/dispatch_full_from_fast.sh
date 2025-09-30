#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/dispatch_full_from_fast.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 HOLDOUT [TRAIN_CLUSTERS] [TOP_N]" >&2
  exit 2
fi
HOLDOUT="$1"
TRAIN="${2:-Abell1689,CL0024}"
TOP_N="${3:-4}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

SEL=$(PYTHONPATH=. ./.venv/bin/python scripts/jobs/select_top_from_fast.py --holdout "$HOLDOUT" --top "$TOP_N" --print || true)
if [ -z "$SEL" ]; then
  echo "[auto-full] No candidates found from FAST runs for $HOLDOUT" >&2
  exit 0
fi

echo "[auto-full] Selected: $SEL" >&2
scripts/jobs/dispatch_bg.sh -n "auto_full_${HOLDOUT}" --scope -- "bash scripts/jobs/batch_w_eff_knee_full_select.sh '$HOLDOUT' '$TRAIN' '$SEL'"

