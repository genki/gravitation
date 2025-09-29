#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.cosmology import Planck18 as cosmo


def arcsec_per_pix_from_wcs(hdr) -> float | None:
    try:
        w = WCS(hdr)
        # compute pixel scale from WCS pixel to world transformation at center
        ny = int(hdr.get('NAXIS2', 0) or 0)
        nx = int(hdr.get('NAXIS1', 0) or 0)
        if nx <= 0 or ny <= 0:
            return None
        x0, y0 = nx/2, ny/2
        # one pixel offset in x
        ra0, dec0 = w.wcs_pix2world([[x0, y0]], 0)[0]
        ra1, dec1 = w.wcs_pix2world([[x0+1, y0]], 0)[0]
        # great-circle distance approx in arcsec
        dra = (ra1 - ra0) * np.cos(np.deg2rad(dec0))
        ddec = (dec1 - dec0)
        ddeg = np.hypot(dra, ddec)
        return float(ddeg * 3600.0)
    except Exception:
        pass
    # fallback to CDELT/CD keywords
    try:
        if 'CDELT1' in hdr and 'CDELT2' in hdr:
            cd1, cd2 = abs(float(hdr['CDELT1'])), abs(float(hdr['CDELT2']))
            return float(3600.0 * max(cd1, cd2))
        # CD matrix
        cd11 = float(hdr.get('CD1_1', 0.0)); cd12 = float(hdr.get('CD1_2', 0.0))
        cd21 = float(hdr.get('CD2_1', 0.0)); cd22 = float(hdr.get('CD2_2', 0.0))
        if any([cd11, cd12, cd21, cd22]):
            # pixel scale as sqrt of determinant components (deg/pix)
            sx = np.hypot(cd11, cd21); sy = np.hypot(cd12, cd22)
            return float(3600.0 * max(sx, sy))
    except Exception:
        return None
    return None


def main() -> int:
    fits_path = Path('data/raw/bullet/1e0657.release1.kappa.if.fits')
    if not fits_path.exists():
        print('error: missing FITS at', fits_path)
        return 1
    with fits.open(fits_path, ignore_missing_simple=True, memmap=False) as hdul:
        hdr = hdul[0].header
    arcsec_per_pix = arcsec_per_pix_from_wcs(hdr)
    if not arcsec_per_pix:
        print('warn: could not derive arcsec/pix from WCS; please set manually in params_cluster.json')
        return 0
    z = 0.296
    DA = cosmo.angular_diameter_distance(z).to('kpc').value  # kpc
    kpc_per_arcsec = DA * (np.pi/648000.0)
    kpc_per_pix = float(kpc_per_arcsec * arcsec_per_pix)
    # update params
    params = Path('data/cluster/params_cluster.json')
    P = {}
    if params.exists():
        P = json.loads(params.read_text(encoding='utf-8'))
    P['scale_kpc_per_pix'] = kpc_per_pix
    params.write_text(json.dumps(P, indent=2), encoding='utf-8')
    print('updated scale_kpc_per_pix =', kpc_per_pix)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

