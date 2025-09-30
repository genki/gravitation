#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/batch_w_eff_knee_full_select.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 HOLDOUT [TRAIN_CLUSTERS] [SELECTED_LIST]" >&2
  echo "  HOLDOUT: e.g., AbellS1063 or MACSJ0416" >&2
  echo "  TRAIN_CLUSTERS: comma-separated (default Abell1689,CL0024)" >&2
  echo "  SELECTED_LIST: 'qk:p:xs,qk:p:xs,...' (default 0.8:1.3:3,0.8:1.3:2,0.7:1.3:3,0.8:1.0:3)" >&2
  exit 2
fi

HOLDOUT="$1"
TRAIN="${2:-Abell1689,CL0024}"
SELECTED="${3:-0.8:1.3:3,0.8:1.3:2,0.7:1.3:3,0.8:1.0:3}"

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "[knee-full] start HOLDOUT=$HOLDOUT TRAIN=$TRAIN SELECTED=$SELECTED"; date -Is

# FULL permutation budget per acceptance criteria
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2 PYTHONMALLOC=malloc

OUTDIR="server/public/reports/holdout_runs"
mkdir -p "$OUTDIR"

IFS=',' read -r -a triples <<< "$SELECTED"
for t in "${triples[@]}"; do
  q="${t%%:*}"; rest="${t#*:}"; p="${rest%%:*}"; xs="${rest#*:}"
  echo "[knee-full] run q_knee=$q p=$p xi_sat=$xs"; date -Is
  BULLET_Q_KNEE="$q" BULLET_P="$p" BULLET_XI_SAT="$xs" \
  PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py \
    --train "$TRAIN" --holdout "$HOLDOUT" --band 8-16 \
    --perm-n 5000 --perm-min 5000 --perm-max 5000 --block-pix 6 || true
  tag="qk${q}_p${p}_xs${xs}"
  if [ -s "server/public/reports/${HOLDOUT}_holdout.json" ]; then
    cp -f "server/public/reports/${HOLDOUT}_holdout.json" "$OUTDIR/${HOLDOUT}_${tag}_full.json" || true
  fi
  if [ -s "server/public/reports/${HOLDOUT}_holdout.html" ]; then
    cp -f "server/public/reports/${HOLDOUT}_holdout.html" "$OUTDIR/${HOLDOUT}_${tag}_full.html" || true
  fi
done

echo "[knee-full] done HOLDOUT=$HOLDOUT"; date -Is

