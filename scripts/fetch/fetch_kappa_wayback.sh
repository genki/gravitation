#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch/fetch_kappa_wayback.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# Generic Wayback-driven κ map fetcher for clusters.
# Usage examples:
#   NAME=Abell1689 bash scripts/fetch/fetch_kappa_wayback.sh
#   NAME=CL0024   bash scripts/fetch/fetch_kappa_wayback.sh
#   NAME=Abell1689 SEEDS="http://example.org/a1689/ http://foo/bar/" PATTERN='(a1689|abell[-_]?1689).*(kappa|mass).*\.(fits|fit)$' bash $0

NAME=${NAME:-}
if [ -z "${NAME}" ]; then
  echo "usage: NAME=<ClusterName> bash $0" >&2
  exit 2
fi

OUTDIR="data/cluster/${NAME}/wayback_hunt"
mkdir -p "$OUTDIR"

# Defaults per cluster (can be overridden via env)
if [ -z "${SEEDS:-}" ]; then
  if [ "$NAME" = "Abell1689" ]; then
    SEEDS=(
      "http://www.ifa.hawaii.edu/~umetsu/GL/galaxy-clusters/abell-1689/"
      "http://www.ifa.hawaii.edu/~umetsu/GL/Abell1689/"
      "http://www.ifa.hawaii.edu/~umetsu/GL/"
      "https://archive.stsci.edu/hlsps/clash/mass/"
      "https://archive.stsci.edu/hlsps/"
    )
    PATTERN='(a1689|abell[-_]?1689).*(kappa|mass2d|mass).*\.(fits|fit)$'
  elif [ "$NAME" = "CL0024" ] || [ "$NAME" = "CL0024+17" ] || [ "$NAME" = "ZwCl0024" ]; then
    SEEDS=(
      "http://www.ifa.hawaii.edu/~umetsu/GL/galaxy-clusters/cl0024/"
      "http://www.ifa.hawaii.edu/~umetsu/GL/CL0024/"
      "http://www.ifa.hawaii.edu/~umetsu/GL/"
    )
    PATTERN='(cl[-_ ]?0024|zwcl[-_ ]?0024).*(kappa|mass2d|mass).*\.(fits|fit)$'
  else
    # Fallback: use provided seeds or do nothing
    echo "[warn] No default SEEDS for $NAME; provide SEEDS=\"url1 url2\" and PATTERN=..." >&2
    SEEDS=()
    PATTERN='(kappa|mass).*\.(fits|fit)$'
  fi
else
  # Split space-separated string into array
  read -r -a SEEDS <<<"${SEEDS}"
fi

echo "[wayback] name=$NAME outdir=$OUTDIR"
printf '[wayback] seeds:\n - %s\n' "${SEEDS[@]:-<none>}"
echo "[wayback] pattern: $PATTERN"

if [ ${#SEEDS[@]} -eq 0 ]; then
  echo "[wayback] No seeds to hunt. Abort." >&2
  exit 1
fi

PYTHONPATH=. ./.venv/bin/python scripts/fetch/wayback_hunt.py \
  --name "$NAME" \
  --pattern "$PATTERN" \
  --seeds "${SEEDS[@]}" \
  --outdir "$OUTDIR" \
  --max-snaps "${MAX_SNAPS:-50}" \
  --max-files "${MAX_FILES:-6}" || true

echo "[wayback] done — see $OUTDIR and wayback_hunt_log.json"
