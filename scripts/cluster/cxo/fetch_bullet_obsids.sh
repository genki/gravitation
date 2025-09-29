#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/cluster/cxo/fetch_bullet_obsids.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
# Fetch Bullet (1E 0657-56) Chandra ObsIDs via CIAO tool and place under data/cluster/Bullet/cxo
# Requires: CIAO 4.17+ active (download_chandra_obsid available)

OBSIDS=(3184 4984 4985 4986 5355 5356 5357 5358 5361)
ROOT="data/cluster/Bullet/cxo"
mkdir -p "$ROOT"
echo "[ciao] Fetching ObsIDs: ${OBSIDS[*]}"
pushd "$ROOT" >/dev/null
for id in "${OBSIDS[@]}"; do
  echo "[ciao] download_chandra_obsid $id evt1,evt2,asol,bpix,mtl,pbk,flt,bias"
  download_chandra_obsid "$id" evt1,evt2,asol,bpix,mtl,pbk,flt,bias || true
done
popd >/dev/null
echo "[ciao] Done. Check $ROOT for ObsID payloads."
