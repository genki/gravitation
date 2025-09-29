#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch/fetch_bullet.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# Bullet Cluster (1E 0657-56) data fetcher
# - Chandra ACIS primary images (full_img2/cntr_img2) from CDA
# - Weak+strong lensing kappa FITS via Wayback (2007-09-10 snapshot)

ROOT="data/cluster/Bullet"
mkdir -p "$ROOT/cxo" "$ROOT/kappa_wayback"

if [ "${SKIP_CXO:-0}" != "1" ]; then
  echo "[bullet] Fetching Chandra ACIS primary images (full_img2/cntr_img2)"
  OBSIDS=(5355 5356 5357 5358 5361 4984 4985 4986 3184)
  for id in "${OBSIDS[@]}"; do
    d=${id: -1}
    for kind in full_img2 cntr_img2; do
      url="https://cxc.cfa.harvard.edu/cdaftp/byobsid/${d}/${id}/primary/acisf0$(printf %04d $id)N004_${kind}.fits.gz"
      echo "[bullet] $url"
      curl -L -C - -o "$ROOT/cxo/$(basename "$url")" "$url" || true
    done
  done
else
  echo "[bullet] SKIP_CXO=1 → skip Chandra ACIS fetch"
fi

echo "[bullet] Fetching kappa/gas/shear from Wayback (Clowe+06 release1)"
SNAP=20070910190709
# Use id_/ form to avoid playback UI redirects and reduce redirect chains
BASE_ID="https://web.archive.org/web/${SNAP}id_/http://flamingos.astro.ufl.edu/1e0657/data"
FILES=(
  1e0657.release1.kappa.fits
  1e0657_central_gasmass_mod.fits
  1e0657.release1.shear.dat
  1e0657.release1.clustergal.dat
)
if [ "${SKIP_WAYBACK:-0}" != "1" ]; then
  fetch_one() {
    local out="$1"; shift
    local tried=0
    for url in "$@"; do
      echo "[bullet] $url"
      if curl --retry 3 --connect-timeout 10 --max-redirs 20 -L -C - -o "$out" "$url"; then
        return 0
      fi
      tried=$((tried+1))
    done
    return 1
  }
  for fn in "${FILES[@]}"; do
    # Try id_ first, then plain (higher redir cap), then http->https variants
    u1="$BASE_ID/$fn"
    u2="https://web.archive.org/web/${SNAP}/http://flamingos.astro.ufl.edu/1e0657/data/$fn"
    u3="https://web.archive.org/web/${SNAP}/https://flamingos.astro.ufl.edu/1e0657/data/$fn"
    fetch_one "$ROOT/kappa_wayback/$fn" "$u1" "$u2" "$u3" || {
      echo "[bullet][WARN] failed to fetch $fn via Wayback"
    }
  done
  echo "[bullet] Copy kappa to kappa_obs.fits"
  cp -f "$ROOT/kappa_wayback/1e0657.release1.kappa.fits" "$ROOT/kappa_obs.fits"
else
  echo "[bullet] SKIP_WAYBACK=1 → skip Wayback fetch"
fi

echo "[bullet] Done. Next: build sigma_e/omega_cut proxies or mosaics, then run: make bullet-holdout"
