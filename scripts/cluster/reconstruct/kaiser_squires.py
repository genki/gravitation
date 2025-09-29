#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
from typing import Tuple
import numpy as np
from astropy.io import fits


def load_shear(path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load a simple shear catalog.
    Expected columns (any delimiter, with header): x y g1 g2 or ra dec g1 g2.
    Units: if RA/Dec, they should already be projected to a local tangent plane in arcsec.
    """
    txt = np.genfromtxt(path, names=True, dtype=None, encoding=None)
    cols = [c.lower() for c in txt.dtype.names]
    def pick(*cands):
        for c in cands:
            if c in cols:
                return txt[c]
        raise KeyError(f"missing any of {cands} in {cols}")
    x = pick('x', 'ra')
    y = pick('y', 'dec')
    g1 = pick('g1', 'e1', 'shear1')
    g2 = pick('g2', 'e2', 'shear2')
    return np.asarray(x, float), np.asarray(y, float), np.asarray(g1, float), np.asarray(g2, float)


def bin_to_grid(x, y, g1, g2, size: int = 256, padding: float = 0.05):
    # Normalize coordinates to [0,1] then map to grid
    xmin, xmax = np.percentile(x, [padding*100, 100 - padding*100])
    ymin, ymax = np.percentile(y, [padding*100, 100 - padding*100])
    xx = (x - xmin) / (xmax - xmin + 1e-9)
    yy = (y - ymin) / (ymax - ymin + 1e-9)
    i = np.clip((yy * (size - 1)).astype(int), 0, size - 1)
    j = np.clip((xx * (size - 1)).astype(int), 0, size - 1)
    # average shears per pixel
    G1 = np.zeros((size, size), float)
    G2 = np.zeros((size, size), float)
    W = np.zeros((size, size), float)
    for ii, jj, a, b in zip(i, j, g1, g2):
        G1[ii, jj] += a
        G2[ii, jj] += b
        W[ii, jj] += 1.0
    W = np.where(W > 0, W, 1.0)
    return G1 / W, G2 / W, W


def kaiser_squires(g1: np.ndarray, g2: np.ndarray) -> np.ndarray:
    """
    Kaiser–Squires inversion in Fourier domain to estimate convergence κ from (g1,g2) ≈ (γ1,γ2)
    assuming weak-lensing limit and flat-sky.
    """
    ny, nx = g1.shape
    # Fourier transforms
    G1 = np.fft.rfft2(g1)
    G2 = np.fft.rfft2(g2)
    ky = np.fft.fftfreq(ny)[:, None]  # cycles per pixel
    kx = np.fft.rfftfreq(nx)[None, :]
    ksq = kx**2 + ky**2
    with np.errstate(divide='ignore', invalid='ignore'):
        P1 = (kx**2 - ky**2) / ksq
        P2 = (2.0 * kx * ky) / ksq
        P1[ksq == 0] = 0.0
        P2[ksq == 0] = 0.0
    K = P1 * G1 + P2 * G2
    kappa = np.fft.irfft2(K, s=(ny, nx))
    # high-pass (remove mean and very-low-k stripe artifacts)
    kappa -= np.nanmean(kappa)
    return kappa


def main() -> int:
    ap = argparse.ArgumentParser(description='Kaiser–Squires κ reconstruction from a shear catalog')
    ap.add_argument('--name', required=True, help='cluster name (for output directory)')
    ap.add_argument('--shear', required=True, type=Path, help='path to shear catalog (ASCII with header: x y g1 g2)')
    ap.add_argument('--size', type=int, default=256, help='grid size (pixels)')
    args = ap.parse_args()

    x, y, g1, g2 = load_shear(args.shear)
    G1, G2, W = bin_to_grid(x, y, g1, g2, size=args.size)
    kappa = kaiser_squires(G1, G2)

    outdir = Path('data/cluster')/args.name
    outdir.mkdir(parents=True, exist_ok=True)
    hdr = fits.Header()
    hdr['HISTORY'] = 'Kaiser–Squires from scripts/cluster/reconstruct/kaiser_squires.py'
    fits.writeto(outdir/'kappa_recon.fits', kappa.astype('f4'), hdr, overwrite=True)
    fits.writeto(outdir/'shear_grid_g1.fits', G1.astype('f4'), hdr, overwrite=True)
    fits.writeto(outdir/'shear_grid_g2.fits', G2.astype('f4'), hdr, overwrite=True)
    fits.writeto(outdir/'shear_grid_w.fits', W.astype('f4'), hdr, overwrite=True)
    print('wrote', outdir/'kappa_recon.fits')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

