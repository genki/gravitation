#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch/fetch_hst_bullet.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# Fetch HST/ACS drizzled products for Bullet (program 10863) via known product name patterns.
# Note: For robust operation, MAST product list API should be queried; here we try common patterns.

OUTDIR="data/cluster/Bullet/hst"
mkdir -p "$OUTDIR"

base='https://mast.stsci.edu/api/v0.1/Download/file?uri='
products=(
  'mast:HST/product/j9e001010_drz.fits'
  'mast:HST/product/j9e001020_drz.fits'
  'mast:HST/product/j9e001030_drz.fits'
  'mast:HST/product/j9e001040_drz.fits'
  'mast:HST/product/j9e001010_drc.fits'
  'mast:HST/product/j9e001020_drc.fits'
)

for prod in "${products[@]}"; do
  url="${base}${prod}"
  fn=$(basename "$prod")
  echo "[hst] $url"
  curl -L -C - -o "$OUTDIR/$fn" "$url" || true
done
echo "[hst] done (some products may be missing; verify in data catalog)"
