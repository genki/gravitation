#!/usr/bin/env python3
from __future__ import annotations
import argparse
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt


def to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img.astype(float)
    if img.ndim == 3 and img.shape[2] >= 3:
        r,g,b = img[...,0], img[...,1], img[...,2]
        return (0.2126*r + 0.7152*g + 0.0722*b).astype(float)
    return img.squeeze().astype(float)


def resample(gray: np.ndarray, size: int = 256) -> np.ndarray:
    import scipy.ndimage as ndi
    ny, nx = gray.shape
    zy, zx = size/ny, size/nx
    out = ndi.zoom(gray, zoom=(zy, zx), order=1)
    vmax = float(np.nanmax(np.abs(out))) or 1.0
    return out / vmax


def convolve_1_over_r(img: np.ndarray) -> np.ndarray:
    ny, nx = img.shape
    y = (np.arange(ny) - (ny - 1) / 2.0)
    x = (np.arange(nx) - (nx - 1) / 2.0)
    yy, xx = np.meshgrid(y, x, indexing='ij')
    r = np.hypot(xx, yy)
    K = 1.0 / np.where(r == 0.0, np.inf, r)
    K = np.fft.ifftshift(K)
    Ik = np.fft.rfftn(img)
    Kk = np.fft.rfftn(K)
    return np.fft.irfftn(Ik * Kk, s=img.shape)


def main() -> int:
    ap = argparse.ArgumentParser(description='Reconstruct approximate kappa via Light-Traces-Mass (LTM) from an optical image (HST composite allowed).')
    ap.add_argument('url', help='URL to optical composite (PNG/JPG/TIF) or local path')
    ap.add_argument('--out', type=Path, default=Path('data/cluster/bullet/kappa.npy'))
    ap.add_argument('--size', type=int, default=256)
    ap.add_argument('--smooth', type=float, default=1.5, help='gaussian sigma (pix) for ICL smoothing')
    args = ap.parse_args()

    # fetch
    p = Path(args.url)
    if '://' in args.url:
        import urllib.request
        tmp = Path('data/cluster/bullet'); tmp.mkdir(parents=True, exist_ok=True)
        p = tmp / 'optical_ltm_src'
        with urllib.request.urlopen(args.url) as r:
            p.write_bytes(r.read())
    img = plt.imread(p)
    gray = to_gray(img)
    # emphasize diffuse ICL by gaussian smoothing and gentle clipping
    import scipy.ndimage as ndi
    g = ndi.gaussian_filter(gray, sigma=float(args.smooth))
    g = np.clip(g, np.nanpercentile(g, 10), np.nanpercentile(g, 99.5))
    g = (g - g.min()) / (g.max() - g.min() + 1e-12)
    g = resample(g, size=int(args.size))
    # LTM: kappa ~ (ICL brightness) * 1/r (proxy)
    kappa = convolve_1_over_r(g)
    kappa /= np.nanmax(np.abs(kappa)) + 1e-12
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.save(args.out, kappa)
    print('wrote', args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

