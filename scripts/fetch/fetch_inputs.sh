#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch/fetch_inputs.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# Create dirs
mkdir -p data/halogas data/sings data/halpha/NGC3198 data/halpha/NGC2403

echo "[fetch] HALOGAS HR moment maps (NGC3198/2403)"
curl -L -C - -o data/halogas/NGC3198-HR_mom1m.fits "https://zenodo.org/record/3715549/files/NGC3198-HR_mom1m.fits?download=1"
curl -L -C - -o data/halogas/NGC3198-HR_mom0m.fits "https://zenodo.org/record/3715549/files/NGC3198-HR_mom0m.fits?download=1"
curl -L -C - -o data/halogas/NGC2403-HR_mom1m.fits "https://zenodo.org/record/3715549/files/NGC2403-HR_mom1m.fits?download=1"
curl -L -C - -o data/halogas/NGC2403-HR_mom0m.fits "https://zenodo.org/record/3715549/files/NGC2403-HR_mom0m.fits?download=1"

echo "[fetch] SINGS Halpha/IRAC (NGC3198/2403)"
curl -L -C - -o data/sings/ngc3198_HA_SUB_dr4.fits \
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/ngc3198/Ancillary/ngc3198_HA_SUB_dr4.fits"
curl -L -C - -o data/sings/ngc3198_irac1.fits \
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/ngc3198/IRAC/ngc3198_v7.phot.1.fits"

curl -L -C - -o data/sings/ngc2403_HA.fits \
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/ngc2403/Ancillary/ngc2403_HA.fits"
curl -L -C - -o data/sings/ngc2403_R.fits  \
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/ngc2403/Ancillary/ngc2403_R.fits"
curl -L -C - -o data/sings/ngc2403_irac1.fits \
  "https://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/ngc2403/IRAC/ngc2403_v7.phot.1.fits"

echo "[fetch] done. Next: ingest Halpha -> EM (see Makefile: ha-ngc3198 / ha-ngc2403)"
