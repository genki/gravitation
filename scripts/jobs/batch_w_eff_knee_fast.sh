#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/batch_w_eff_knee_fast.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 HOLDOUT [TRAIN_CLUSTERS]" >&2
  echo "  HOLDOUT: e.g. AbellS1063 or MACSJ0416" >&2
  echo "  TRAIN_CLUSTERS (optional, default Abell1689,CL0024)" >&2
  exit 2
fi

HOLDOUT="$1"
TRAIN="${2:-Abell1689,CL0024}"
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

# FAST grid per A-3: smaller perm budget via --fast (target≈1200, min≈600, early-stop)
Q_LIST=(0.6 0.7 0.8)
P_LIST=(0.7 1.0 1.3)
XI_SAT_LIST=(1 2 3)

COMMON_ENV="OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2 PYTHONMALLOC=malloc"
BASE_CMD="PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py --train $TRAIN --holdout $HOLDOUT --band 8-16 --fast --block-pix 6"

# Compose a single sequential command string to run under dispatcher
CMD_STR="set -e; echo 'A-3 FAST knee grid start: $HOLDOUT'"$'\n'
for q in "${Q_LIST[@]}"; do
  for p in "${P_LIST[@]}"; do
    for xs in "${XI_SAT_LIST[@]}"; do
      CMD_STR+=" ${COMMON_ENV} BULLET_Q_KNEE=${q} BULLET_P=${p} BULLET_XI_SAT=${xs} ${BASE_CMD}"$'\n'
    done
  done
done
CMD_STR+=$'echo "A-3 FAST knee grid done: '$HOLDOUT'"\n'

scripts/jobs/dispatch_bg.sh -n "w_eff_knee_fast_${HOLDOUT}" --cwd "$REPO_ROOT" --env "$COMMON_ENV" --scope -- "$CMD_STR"

