#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/watch_collect_a4.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

HOLDOUT="${1:-AbellS1063}"
INTERVAL="${2:-60}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

SNAP_DIR="server/public/reports/a4_fast/${HOLDOUT}"
OUT_HTML="server/public/reports/${HOLDOUT}_a4_summary.html"
mkdir -p "$SNAP_DIR"

echo "[watch-a4] collecting every ${INTERVAL}s for $HOLDOUT (snapshots: $SNAP_DIR)" >&2
while true; do
  PYTHONPATH=. ./.venv/bin/python scripts/jobs/collect_a4_fast_runs.py --holdout "$HOLDOUT" --out "$OUT_HTML" >/dev/null 2>&1 || true
  sleep "$INTERVAL"
done

