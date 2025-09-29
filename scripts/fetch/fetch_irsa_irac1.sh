#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch/fetch_irsa_irac1.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# Try multiple IRSA SINGS IRAC1 (3.6um) endpoints and filenames, validate FITS.
# Usage: NAME=NGC3198 bash scripts/fetch/fetch_irsa_irac1.sh

NAME=${NAME:-}
if [ -z "${NAME}" ]; then
  echo "usage: NAME=<NGCname> bash $0" >&2
  exit 2
fi

OUTDIR="data/sings"
mkdir -p "$OUTDIR"

lower=$(echo "$NAME" | tr 'A-Z' 'a-z')
targets=(
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/irac/${lower}_irac1.fits"
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/irac/${lower}_irac_ch1_mosaic.fits"
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/irac/${lower}_irac_ch1.fits"
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/irac/mosaics/${lower}_irac_ch1_mosaic.fits"
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/irac/mosaics/${lower}_irac1_mosaic.fits"
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/IRAC/${lower}_irac1.fits"
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/IRAC/${lower}_irac_ch1.fits"
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/IRAC/${lower}_irac_ch1_mosaic.fits"
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/IRAC/${lower}_v7.phot.1.fits"
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/${lower}/IRAC/${lower}_v7.phot.1_wt.fits"
)

validate_fits() {
  ./.venv/bin/python - "$1" << 'PY'
import sys
from astropy.io import fits
from pathlib import Path
p=Path(sys.argv[1])
ok=False
try:
    hdul=fits.open(p)
    ok=bool(hdul) and (hdul[0].header.get('SIMPLE', True) is not False)
except Exception:
    ok=False
print('OK' if ok and p.stat().st_size>100000 else 'NG')
PY
}

for url in "${targets[@]}"; do
  fn=$(basename "$url")
  out="$OUTDIR/${fn}"
  echo "[irsa] $url"
  curl -L -C - -o "$out" "$url" || true
  if [ -s "$out" ]; then
    res=$(validate_fits "$out" || echo NG)
    if [ "$res" = "OK" ]; then
      echo "[irsa] saved $out"
      exit 0
    else
      echo "[irsa] invalid FITS (likely HTML placeholder): $out; removing"
      rm -f "$out"
    fi
  fi
done
echo "[irsa][WARN] failed to fetch valid IRAC1 for $NAME"
exit 1
