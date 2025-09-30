#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/batch_se_psf_grid_fast_subset.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

HOLDOUT="${1:-AbellS1063}"
TRAIN="${2:-Abell1689,CL0024}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

SE_LIST=(none asinh)
PSF_LIST=(1.5)
HP_LIST=(8)

COMMON_ENV="OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2 PYTHONMALLOC=malloc"
# Export memory/threads caps once for this script
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export NUMEXPR_MAX_THREADS=1
export MALLOC_ARENA_MAX=2
export PYTHONMALLOC=malloc
SAVE_DIR="server/public/reports/a4_fast/${HOLDOUT}"
mkdir -p "$SAVE_DIR"

echo "[subset] A-4 FAST subset start: $HOLDOUT" >&2
for se in "${SE_LIST[@]}"; do
  for psf in "${PSF_LIST[@]}"; do
    for hp in "${HP_LIST[@]}"; do
      echo "[subset] run se=$se psf=$psf hp=$hp" >&2
      BULLET_SE_TRANSFORM=${se} PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
        --train "$TRAIN" --holdout "$HOLDOUT" --sigma-psf "$psf" --sigma-highpass "$hp" --band 8-16 --fast --block-pix 6 || true
      STAMP=$(date +%Y%m%d_%H%M%S)
      cp -f "server/public/reports/cluster/${HOLDOUT}_holdout.json" "${SAVE_DIR}/${STAMP}_se-${se}_psf-${psf}_hp-${hp}.json" 2>/dev/null || true
      cp -f "server/public/reports/${HOLDOUT}_holdout.html" "${SAVE_DIR}/${STAMP}_se-${se}_psf-${psf}_hp-${hp}.html" 2>/dev/null || true
      PYTHONPATH=. ./.venv/bin/python scripts/jobs/collect_a4_fast_runs.py --holdout "$HOLDOUT" --out "server/public/reports/${HOLDOUT}_a4_summary.html" 2>/dev/null || true
    done
  done
done
echo "[subset] A-4 FAST subset done: $HOLDOUT" >&2
