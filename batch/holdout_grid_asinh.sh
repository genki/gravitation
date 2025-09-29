#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run batch/holdout_grid_asinh.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/_common.sh"

# Defaults (override via env or passing HP list as args)
: "${BULLET_W_POWER_FORCE:=0.1}"
: "${BULLET_PERM_N:=5000}"
: "${BULLET_BOOT_N:=4096}"
: "${SE_TRANSFORM:=asinh}"
: "${BETA_SWEEP:=0.6,0.8,1.0}"
: "${PSF_LIST:=1.2,1.5,1.8}"

HP_LIST=("6" "7" "9")
if [[ $# -gt 0 ]]; then HP_LIST=("$@"); fi

total=${#HP_LIST[@]}
idx=0
start_ts=$(date +%s)
for HP in "${HP_LIST[@]}"; do
  idx=$((idx+1))
  echo "[holdout] HP=$HP, PSF=$PSF_LIST, β=$BETA_SWEEP, SE_TRANSFORM=$SE_TRANSFORM, w^$BULLET_W_POWER_FORCE"
  PYTHONUNBUFFERED=1 BULLET_W_POWER_FORCE=$BULLET_W_POWER_FORCE BULLET_PERM_N=$BULLET_PERM_N BULLET_BOOT_N=$BULLET_BOOT_N FAST_HOLDOUT=0 \
    python -u "$REPO_ROOT/scripts/reports/make_bullet_holdout.py" \
      --beta-sweep "$BETA_SWEEP" --sigma-psf "$PSF_LIST" --sigma-highpass "$HP" --se-transform "$SE_TRANSFORM" \
      2>&1 | tee "$LOG_DIR/holdout_asinh_hp${HP}.log"
  ts=$(date +%Y%m%d_%H%M%S)
  cp -f "$REPO_ROOT/server/public/reports/bullet_holdout.json" "$REPO_ROOT/server/public/reports/bullet_holdout_asinh_hp${HP}_${ts}.json"
  cp -f "$REPO_ROOT/server/public/reports/bullet_holdout.html" "$REPO_ROOT/server/public/reports/bullet_holdout_asinh_hp${HP}_${ts}.html"
  now=$(date +%s); elapsed=$((now-start_ts)); avg=$((elapsed/idx)); rem=$((total-idx)); eta=$((avg*rem))
  printf '[holdout][%d/%d] elapsed=%dm ETA=%dm\n' "$idx" "$total" "$((elapsed/60))" "$((eta/60))"
done

echo "[holdout] done. Snapshots saved under server/public/reports/"
