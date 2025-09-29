#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run batch/train_asinh_knee_multiscale.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/_common.sh"

# Defaults (can be overridden via environment or batch/config.env)
: "${W_CORR_FRAC:=0.10}"
: "${SE_TRANSFORM:=asinh}"
: "${GATE_SIGMAS:=2,4,8}"
: "${GRID_S_GATE:=16,24,32}"
: "${GRID_Q_KNEE:=0.6,0.7,0.8}"
: "${GRID_XI:=1.2,2.4,3.6}"
: "${GRID_XI_SAT:=1.0,0.5,0.3333}"
: "${GRID_P:=0.7,1.0,1.3}"
: "${GRID_TAUQ:=0.70,0.75,0.80}"

DT_LIST=("0.10" "0.15" "0.20")
if [[ $# -gt 0 ]]; then
  DT_LIST=("$@")
fi

total=${#DT_LIST[@]}
idx=0
start_ts=$(date +%s)
for DT in "${DT_LIST[@]}"; do
  idx=$((idx+1))
  echo "[train] dtfrac=$DT  (W_CORR_FRAC=$W_CORR_FRAC, SE_TRANSFORM=$SE_TRANSFORM, GATE_SIGMAS=$GATE_SIGMAS)"
  PYTHONUNBUFFERED=1 W_CORR_FRAC=$W_CORR_FRAC SE_TRANSFORM=$SE_TRANSFORM GATE_SIGMAS=$GATE_SIGMAS \
  GRID_S_GATE=$GRID_S_GATE GRID_Q_KNEE=$GRID_Q_KNEE GRID_XI=$GRID_XI \
  GRID_XI_SAT=$GRID_XI_SAT GRID_P=$GRID_P GRID_TAUQ=$GRID_TAUQ \
  GRID_DELTA_TAU_FRAC=$DT \
  python -u "$REPO_ROOT/scripts/cluster/fit/train_shared_params.py" \
    2>&1 | tee "$LOG_DIR/train_asinh_knee_multiscale_dt${DT}.log"
  now=$(date +%s); elapsed=$((now-start_ts)); avg=$((elapsed/idx)); rem=$((total-idx)); eta=$((avg*rem))
  printf '[train][%d/%d] elapsed=%dm ETA=%dm\n' "$idx" "$total" "$((elapsed/60))" "$((eta/60))"
done

echo "[train] done. params saved to data/cluster/params_cluster.json"
