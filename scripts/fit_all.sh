#!/usr/bin/env bash
# Guard to avoid leaking strict mode when sourced accidentally
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fit_all.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# End-to-end pipeline runner for reproducible SOTA updates.
# Steps:
#  1) Build subsets (lsb/hsb, q1-3, clean sets)
#  2) Shared-parameter fits (all / noBL / subsets)
#  3) Cross-validation summaries
#  4) Site SOTA rebuild and E2E checks

PY=${PY:-.venv/bin/python}

echo "[1/4] Make subsets"
PYTHONPATH=. "$PY" scripts/make_subsets.py || true

echo "[2/4] Shared fits"
mkdir -p data/results
# Full set (may be slow on first run); chunk execution to keep each run bounded
MAX_MINUTES=${FIT_ALL_MAX_MINUTES:-55} \
CHUNK_SIZE=${FIT_ALL_CHUNK_SIZE:-0} \
RESET_PROGRESS=${FIT_ALL_RESET_PROGRESS:-0} \
PY=${PY} \
  ./scripts/compare_fit_multi_chunked.sh \
  --names-file data/sparc/sets/clean_for_fit.txt \
  --lam-grid 18,20,22,24 --A-grid 100,112,125 --gas-scale-grid 1.0,1.33 \
  --err-floor-kms 5 --pad-factor 2 --auto-geo --boost 0.5 --boost-tie-lam \
  --out data/results/multi_fit_clean.json || true

# noBL subsets
for tag in lsb_noBL hsb_noBL; do
  nf="data/sparc/sets/${tag}.txt"
  if [ -f "$nf" ]; then
    MAX_MINUTES=${FIT_ALL_MAX_MINUTES:-55} \
    CHUNK_SIZE=${FIT_ALL_CHUNK_SIZE:-0} \
    RESET_PROGRESS=${FIT_ALL_RESET_PROGRESS:-0} \
    PY=${PY} \
      ./scripts/compare_fit_multi_chunked.sh --names-file "$nf" \
      --lam-grid 18,20,22,24 --A-grid 100,112,125 --gas-scale-grid 1.0,1.33 \
      --err-floor-kms 5 --pad-factor 2 --auto-geo --boost 0.5 --boost-tie-lam \
      --out "data/results/multi_fit_${tag}.json" || true
  fi
done

echo "[3/4] Cross-validation"
PYTHONPATH=. "$PY" scripts/cross_validate_shared.py --names-file data/sparc/sets/clean_for_fit.txt \
  --out-prefix cv_shared_summary || true

echo "[4/4] Rebuild SOTA + E2E"
PYTHONPATH=. "$PY" scripts/build_state_of_the_art.py || true
PYTHONPATH=. "$PY" scripts/e2e_site_check.py || true

echo "fit_all done."
