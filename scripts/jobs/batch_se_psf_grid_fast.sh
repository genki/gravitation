#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/jobs/batch_se_psf_grid_fast.sh" >&2
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

# FAST grid for A-4 (se_transform × psf × highpass) using --fast to rank candidates
SE_LIST=(none asinh log1p rank)
PSF_LIST=(1.2 1.5 1.8)
HP_LIST=(6 8 10)

COMMON_ENV="OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2 PYTHONMALLOC=malloc"

# Save per-run artifacts to avoid overwrite and enable later aggregation
SAVE_DIR="server/public/reports/a4_fast/${HOLDOUT}"
mkdir -p "$SAVE_DIR"

CMD_STR="set -e; echo 'A-4 FAST se×psf×hp start: $HOLDOUT'"$'\n'
for se in "${SE_LIST[@]}"; do
  for psf in "${PSF_LIST[@]}"; do
    for hp in "${HP_LIST[@]}"; do
      CMD_STR+=" ${COMMON_ENV} BULLET_SE_TRANSFORM=${se} PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py --train $TRAIN --holdout $HOLDOUT --sigma-psf ${psf} --sigma-highpass ${hp} --band 8-16 --fast --block-pix 6"$'\n'
      # Copy snapshot of JSON/HTML with a unique name for aggregation
      CMD_STR+=" STAMP=\$(date +%Y%m%d_%H%M%S)"$'\n'
      CMD_STR+=" cp -f server/public/reports/cluster/${HOLDOUT}_holdout.json '${SAVE_DIR}/'\"\${STAMP}\"'_se-'${se}'_psf-'${psf}'_hp-'${hp}'.json' 2>/dev/null || true"$'\n'
      CMD_STR+=" cp -f server/public/reports/${HOLDOUT}_holdout.html '${SAVE_DIR}/'\"\${STAMP}\"'_se-'${se}'_psf-'${psf}'_hp-'${hp}'.html' 2>/dev/null || true"$'\n'
      # Update summary table (best-effort)
      CMD_STR+=" PYTHONPATH=. ./.venv/bin/python scripts/jobs/collect_a4_fast_runs.py --holdout '$HOLDOUT' --out 'server/public/reports/${HOLDOUT}_a4_summary.html' 2>/dev/null || true"$'\n'
    done
  done
done
CMD_STR+=$'echo "A-4 FAST se×psf×hp done: '$HOLDOUT'"\n'

scripts/jobs/dispatch_bg.sh -n "sepsf_grid_fast_${HOLDOUT}" --cwd "$REPO_ROOT" --env "$COMMON_ENV" --scope -- "$CMD_STR"
