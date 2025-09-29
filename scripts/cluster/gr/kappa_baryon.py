#!/usr/bin/env python3
from __future__ import annotations
import json
import numpy as np
from pathlib import Path


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
    # Use gas (Sigma_e) as proxy; optional optical LTM if available to add stellar term
    sigma = np.load('data/cluster/maps/bullet_sigma_e.npy')
    kappa_gr = convolve_1_over_r(sigma)
    # Optional optical LTM contribution
    ltm = Path('data/cluster/bullet/kappa.npy')
    if ltm.exists():
        try:
            kappa_stars = np.load(ltm)
            # resample to sigma grid if needed
            if kappa_stars.shape != sigma.shape:
                import scipy.ndimage as ndi
                zy, zx = sigma.shape[0]/kappa_stars.shape[0], sigma.shape[1]/kappa_stars.shape[1]
                kappa_stars = ndi.zoom(kappa_stars, zoom=(zy, zx), order=1)
            # blend: stars (ltm) + gas (sigma_e)
            kappa_gr = 0.5 * kappa_gr + 0.5 * kappa_stars
        except Exception:
            pass
    # Normalize
    vmax = float(np.nanmax(np.abs(kappa_gr))) or 1.0
    kappa_gr = kappa_gr / vmax
    out = Path('data/cluster/gr'); out.mkdir(parents=True, exist_ok=True)
    np.save(out / 'bullet_kappa_gr.npy', kappa_gr)
    print('wrote', out / 'bullet_kappa_gr.npy')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

