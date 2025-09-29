#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/run_w_eff_knee_fast_seq.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 HOLDOUT [TRAIN_CLUSTERS]" >&2
  exit 2
fi

HOLDOUT="$1"
TRAIN="${2:-Abell1689,CL0024}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

Q_LIST=(0.6 0.7 0.8)
P_LIST=(0.7 1.0 1.3)
XI_SAT_LIST=(1 2 3)

echo "[knee-fast] start HOLDOUT=$HOLDOUT TRAIN=$TRAIN"; date -Is

export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2 PYTHONMALLOC=malloc

for q in "${Q_LIST[@]}"; do
  for p in "${P_LIST[@]}"; do
    for xs in "${XI_SAT_LIST[@]}"; do
      echo "[knee-fast] run q_knee=$q p=$p xi_sat=$xs"; date -Is
      BULLET_Q_KNEE="$q" BULLET_P="$p" BULLET_XI_SAT="$xs" \
      PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
        --train "$TRAIN" --holdout "$HOLDOUT" --band 8-16 --fast --block-pix 6 || true
    done
  done
done

echo "[knee-fast] done HOLDOUT=$HOLDOUT"; date -Is

