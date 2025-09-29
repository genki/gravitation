#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from astropy.io import fits


def spectral_axis_kms(hdr: fits.Header, nchan: int) -> np.ndarray:
    # Build spectral coordinate [km/s] from FITS WCS keywords (CRVAL3, CDELT3, CRPIX3)
    crval = float(hdr.get('CRVAL3', 0.0))
    cdelt = float(hdr.get('CDELT3', 1.0))
    crpix = float(hdr.get('CRPIX3', 1.0))
    idx = np.arange(1, nchan + 1, dtype=float)
    v = crval + (idx - crpix) * cdelt  # native unit (likely m/s)
    # Heuristic: if unit is m/s scale (|v|~1e5..1e6), convert to km/s
    if np.nanmedian(np.abs(v)) > 1e3:
        v = v / 1.0e3
    return v.astype(float)


def moment1(cube: np.ndarray, v_kms: np.ndarray, snr_thr: float | None = None) -> np.ndarray:
    # cube: (nz, ny, nx). Use simple intensity-weighted mean along axis 0.
    data = np.nan_to_num(cube, nan=0.0)
    if snr_thr and snr_thr > 0:
        # crude noise estimate per pixel: robust MAD across channels
        mad = np.nanmedian(np.abs(data - np.nanmedian(data, axis=0, keepdims=True)), axis=0)
        sig = 1.4826 * mad
        mask = data >= (snr_thr * sig)
        data = np.where(mask, data, 0.0)
    w = data
    num = np.tensordot(v_kms, w, axes=(0, 0))  # (ny,nx)
    den = np.sum(w, axis=0) + 1e-30
    m1 = num / den
    return m1.astype(np.float32)


def main() -> int:
    ap = argparse.ArgumentParser(description='Make moment-1 (velocity) map from a HI cube')
    ap.add_argument('--cube', type=Path, required=True, help='input cube FITS')
    ap.add_argument('--out', type=Path, required=True, help='output moment-1 FITS (km/s)')
    ap.add_argument('--snr-thr', type=float, default=0.0, help='per-pixel SNR threshold (~sigma)')
    args = ap.parse_args()
    with fits.open(args.cube) as hdul:
        data = hdul[0].data.astype(float)
        hdr = hdul[0].header.copy()
    # Try to standardize axis order to (nz, ny, nx)
    if data.ndim == 4:
        # some cubes: (stokes, nz, ny, nx) with stokes=1
        data = data[0]
    if data.shape[0] < data.shape[-1]:
        # assume first is spectral already (nz, ny, nx)
        pass
    v_kms = spectral_axis_kms(hdr, data.shape[0])
    mom1 = moment1(data, v_kms, snr_thr=float(args.snr_thr or 0.0))
    ohdr = hdr.copy()
    # Remove spectral axis keywords (collapse), set units
    for k in ['CRVAL3','CDELT3','CRPIX3','CTYPE3','CUNIT3','NAXIS3']:
        if k in ohdr: del ohdr[k]
    ohdr['NAXIS'] = 2
    ohdr['BUNIT'] = 'km/s'
    fits.writeto(args.out, mom1, ohdr, overwrite=True)
    print('wrote', args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

