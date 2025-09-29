#!/usr/bin/env python3
from __future__ import annotations

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path


def _gaussian_random_field(n: int = 256, k0: float = 4.0, seed: int = 1234) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # Fourier-space amplitudes with P(k) ~ 1/(k^2 + k0^2)
    kx = np.fft.fftfreq(n) * n
    ky = np.fft.fftfreq(n) * n
    KX, KY = np.meshgrid(kx, ky, indexing='xy')
    K2 = KX*KX + KY*KY
    amp = 1.0 / (K2 + k0*k0)
    phase = rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))
    F = phase * np.sqrt(np.maximum(amp, 1e-12))
    x = np.fft.ifft2(F).real
    x -= x.mean(); x /= (x.std() + 1e-12)
    return x


def _grad_mag(x: np.ndarray) -> np.ndarray:
    gx, gy = np.gradient(x)
    g = np.sqrt(gx*gx + gy*gy)
    g /= (np.percentile(g, 99) + 1e-12)
    return np.clip(g, 0.0, 1.5)


def _sample_points_by_weight(w: np.ndarray, n_pts: int, rng: np.random.Generator) -> np.ndarray:
    h, wW = w.shape
    p = w.ravel().astype(float)
    p = np.maximum(p, 0.0)
    if p.sum() <= 0:
        p = np.ones_like(p)
    p = p / p.sum()
    idx = rng.choice(p.size, size=n_pts, replace=True, p=p)
    y = idx // wW
    x = idx % wW
    pts = np.stack([x + rng.uniform(0,1,size=n_pts), y + rng.uniform(0,1,size=n_pts)], axis=-1)
    return pts


def _cross_corr_radial(a: np.ndarray, b: np.ndarray, nbins: int = 40) -> tuple[np.ndarray, np.ndarray]:
    # Normalize each field
    a0 = (a - a.mean()) / (a.std() + 1e-12)
    b0 = (b - b.mean()) / (b.std() + 1e-12)
    n = a.shape[0]
    # FFT-based correlation of (a0) with (b0)
    A = np.fft.rfftn(a0)
    B = np.fft.rfftn(b0)
    C = np.fft.irfftn(A * np.conj(B), s=a0.shape)
    # Radial average from center
    yy, xx = np.indices(a.shape)
    cx, cy = (n/2, n/2)
    r = np.sqrt((xx - cx)**2 + (yy - cy)**2)
    rmax = r.max()
    bins = np.linspace(0, rmax, nbins+1)
    rad = 0.5 * (bins[1:] + bins[:-1])
    prof = np.zeros(nbins)
    for i in range(nbins):
        m = (r >= bins[i]) & (r < bins[i+1])
        prof[i] = float(C[m].mean()) if np.any(m) else 0.0
    # Normalize profile to unity at r=0 for visualization
    if prof[0] != 0:
        prof = prof / abs(prof[0])
    return rad, prof


def generate_eu5(out_dir: Path | None = None, n: int = 256, n_gal: int = 600) -> Path:
    out_dir = out_dir or Path('assets/figures/early_universe')
    out_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(777)
    # 21 cm brightness temperature proxy (GRF) and boundary strength
    Tb = _gaussian_random_field(n=n, k0=6.0, seed=2025)
    G = _grad_mag(Tb)
    # Galaxy density proxy biased to high |∇Tb|
    pts = _sample_points_by_weight(G**1.5, n_gal, rng)
    gal = np.zeros_like(Tb)
    for (x, y) in pts.astype(int):
        gal[y, x] += 1.0
    # Smooth galaxy map slightly for correlation
    from scipy.ndimage import gaussian_filter
    gal_s = gaussian_filter(gal, sigma=1.0)
    # Cross-correlation radial profile
    r, prof = _cross_corr_radial(G, gal_s, nbins=40)

    # Figure: 2x2 panels
    fig, axes = plt.subplots(2, 2, figsize=(8, 7))
    im0 = axes[0,0].imshow(Tb, cmap='magma'); axes[0,0].set_title('Tb (21 cm; GRF proxy)'); plt.colorbar(im0, ax=axes[0,0], fraction=0.046)
    im1 = axes[0,1].imshow(G, cmap='viridis'); axes[0,1].set_title('|∇Tb| (boundary strength)'); plt.colorbar(im1, ax=axes[0,1], fraction=0.046)
    axes[1,0].imshow(G, cmap='viridis'); axes[1,0].scatter(pts[:,0], pts[:,1], s=6, c='white', alpha=0.7, edgecolors='none'); axes[1,0].set_title('Galaxies biased to high |∇Tb|')
    axes[1,1].plot(r, prof, 'C3-'); axes[1,1].set_title('Cross-correlation (normed)'); axes[1,1].set_xlabel('radius [px]'); axes[1,1].set_ylabel('ξ(0)=1')
    for ax in axes.ravel():
        ax.set_xticks([]); ax.set_yticks([])
    plt.tight_layout()
    out = out_dir / 'Fig-EU5_21cm_corr.png'
    plt.savefig(out, dpi=160)
    plt.close()
    return out


def main() -> int:
    out = generate_eu5()
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

