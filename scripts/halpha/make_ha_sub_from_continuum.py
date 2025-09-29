#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from astropy.io import fits


def compute_scale(H: np.ndarray, C: np.ndarray) -> float:
    # Robust L2 scaling on low-H pixels (exclude bright emission tail)
    Hf = H[np.isfinite(H)]
    thr = np.nanpercentile(Hf, 95) if Hf.size else np.nan
    m = np.isfinite(H) & np.isfinite(C)
    if np.isfinite(thr):
        m &= (H <= thr)
    h = H[m].astype(float)
    c = C[m].astype(float)
    c2 = np.sum(c * c)
    if c2 <= 0:
        return 0.0
    a = float(np.sum(c * h) / c2)
    return max(a, 0.0)


def main() -> int:
    ap = argparse.ArgumentParser(description='Construct HA_SUB = HA - a * CONT (continuum)')
    ap.add_argument('--ha', type=Path, required=True, help='Halpha image (narrowband, counts or cps)')
    ap.add_argument('--cont', type=Path, required=True, help='continuum image (e.g., R band)')
    ap.add_argument('--out', type=Path, required=True, help='output HA_SUB FITS (same grid)')
    args = ap.parse_args()
    h = fits.getdata(args.ha).astype(float)
    c = fits.getdata(args.cont).astype(float)
    if h.shape != c.shape:
        print('ERROR: shapes differ; reproject not implemented. Provide matched grid.', h.shape, c.shape)
        return 2
    a = compute_scale(h, c)
    sub = h - a * c
    hdr = fits.getheader(args.ha).copy()
    hdr['HAC_CONT'] = (args.cont.name, 'continuum image used')
    hdr['HAC_ALPHA'] = (float(a), 'continuum scale factor')
    fits.writeto(args.out, sub.astype(np.float32), hdr, overwrite=True)
    print('wrote', args.out, 'with alpha=', a)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

