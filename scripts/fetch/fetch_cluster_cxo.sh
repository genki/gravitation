#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch/fetch_cluster_cxo.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# Generic Chandra ACIS primary fetcher for a cluster.
# Usage:
#   NAME=Abell1689 OBSIDS="5004 540 1663" bash scripts/fetch/fetch_cluster_cxo.sh

NAME=${NAME:-}
OBSIDS=${OBSIDS:-}
if [ -z "${NAME}" ] || [ -z "${OBSIDS}" ]; then
  echo "usage: NAME=<ClusterName> OBSIDS=\"<space-separated obsids>\" bash $0" >&2
  echo "example: NAME=Abell1689 OBSIDS=\"540 1663 5004 6930\" bash $0" >&2
  exit 2
fi

ROOT="data/cluster/${NAME}"
mkdir -p "$ROOT/cxo"
echo "[cxo] target=$NAME obsids=($OBSIDS)"
for id in $OBSIDS; do
  d=${id: -1}
  for kind in full_img2 cntr_img2; do
    url="https://cxc.cfa.harvard.edu/cdaftp/byobsid/${d}/${id}/primary/acisf0$(printf %04d $id)N004_${kind}.fits.gz"
    echo "[cxo] $url"
    curl -L -C - -o "$ROOT/cxo/$(basename "$url")" "$url" || true
  done
done
echo "[cxo] done: $ROOT/cxo"
