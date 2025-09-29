#!/usr/bin/env python3
from __future__ import annotations
import sys
import argparse
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt


def save_resampled(arr: np.ndarray, out: Path, size: int = 256) -> None:
    import scipy.ndimage as ndi
    ny, nx = arr.shape
    zy, zx = size / ny, size / nx
    out_arr = ndi.zoom(arr.astype(float), zoom=(zy, zx), order=1)
    # normalize to 0..1 for sanity
    vmax = float(np.nanmax(np.abs(out_arr))) or 1.0
    out_arr = out_arr / vmax
    np.save(out, out_arr)
    print('wrote', out, out_arr.shape, out_arr.dtype)


def fetch(url: str, dst: Path) -> None:
    import urllib.request
    with urllib.request.urlopen(url) as r:
        data = r.read()
    dst.write_bytes(data)
    print('downloaded', url, '->', dst)


def main() -> int:
    ap = argparse.ArgumentParser(description='Fetch Bullet Cluster kappa map and convert to npy')
    ap.add_argument('url', help='URL to FITS/PNG/JPG/TIF of kappa map')
    ap.add_argument('--out', type=Path, default=Path('data/cluster/bullet/kappa.npy'))
    args = ap.parse_args()
    tmp = Path('data/cluster/bullet'); tmp.mkdir(parents=True, exist_ok=True)
    cache = tmp / 'kappa_download'
    fetch(args.url, cache)
    # Try FITS first (extension may be missing in archived downloads)
    try:
        from astropy.io import fits
        with fits.open(cache, ignore_missing_simple=True, memmap=False) as hdul:
            arr = hdul[0].data.astype(float)
        if arr.ndim > 2:
            arr = arr.squeeze()
        save_resampled(arr, args.out)
        return 0
    except Exception as e:
        print('info: FITS read attempt failed, will try as image:', e)
    ext = cache.suffix.lower()
    if ext in ('.fits', '.fit'):
        try:
            from astropy.io import fits
            arr = fits.getdata(cache).astype(float)
            if arr.ndim > 2: arr = arr.squeeze()
            save_resampled(arr, args.out)
            return 0
        except Exception as e:
            print('warn: FITS read failed (astropy missing or read error):', e)
            # fallback: keep FITS alongside
            out_fits = Path('data/cluster/bullet/kappa.fits')
            out_fits.write_bytes(cache.read_bytes())
            print('saved FITS to', out_fits, '— install astropy to convert to npy')
            return 0
    # Fallback: image reader
    img = plt.imread(cache)
    if img.ndim == 3 and img.shape[2] >= 3:
        r,g,b = img[...,0], img[...,1], img[...,2]
        arr = 0.2126*r + 0.7152*g + 0.0722*b
    else:
        arr = img.squeeze()
    save_resampled(arr, args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
