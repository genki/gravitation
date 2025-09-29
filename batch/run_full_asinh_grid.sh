#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run batch/run_full_asinh_grid.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/_common.sh"

# Optional: load overrides
if [[ -f "$HERE/config.env" ]]; then
  # shellcheck disable=SC1090
  source "$HERE/config.env"
fi

DT_LIST=("0.10" "0.15" "0.20")
HP_LIST=("6" "7" "9")

# 1) Train across dtfrac list
"$HERE/train_asinh_knee_multiscale.sh" "${DT_LIST[@]}"

# 2) Constrained β search (uses latest params_cluster.json)
"$HERE/search_beta.sh"

# 3) Holdout across high-pass list
"$HERE/holdout_grid_asinh.sh" "${HP_LIST[@]}"

echo "[batch] Completed full asinh+knee+multiscale grid. See server/public/reports/ for outputs."
