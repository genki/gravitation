#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run batch/search_beta.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/_common.sh"

: "${GRID_BETA:=0.6,0.8,1.0}"

echo "[search] constrained β search with GRID_BETA=$GRID_BETA"
start_ts=$(date +%s)
PYTHONUNBUFFERED=1 GRID_BETA=$GRID_BETA python -u "$REPO_ROOT/scripts/cluster/fit/holdout_constrained_search.py" \
  2>&1 | tee "$LOG_DIR/search_beta.log"
elapsed=$(( $(date +%s) - start_ts ))
printf '[search] done in %dm\n' "$((elapsed/60))"

echo "[search] wrote server/public/reports/bullet_holdout_search.json"
