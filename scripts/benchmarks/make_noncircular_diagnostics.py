#!/usr/bin/env python3
from __future__ import annotations
"""Non-circular diagnostics for a galaxy velocity field.

Outputs panel images of:
 - residual (ring-median subtracted)
 - m=1 (lopsided/warp) azimuthal harmonic amplitude map
 - m=2 (bar/spiral) azimuthal harmonic amplitude map
Optionally overlays Halpha contours if available.
"""
import argparse
from pathlib import Path
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def ring_median_residual(v: np.ndarray, nbins: int = 64) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    ny, nx = v.shape
    yy, xx = np.indices((ny, nx))
    cy, cx = (ny - 1) / 2.0, (nx - 1) / 2.0
    x = xx - cx; y = yy - cy
    r = np.hypot(x, y)
    theta = np.arctan2(y, x)
    rmax = r.max(); edges = np.linspace(0, rmax, nbins + 1)
    med = np.zeros_like(v) + np.nan
    for i in range(nbins):
        m = (r >= edges[i]) & (r < edges[i+1]) & np.isfinite(v)
        if not m.any():
            continue
        rv = np.nanmedian(v[m])
        med[m] = rv
    resid = v - med
    return resid, r, theta, edges, med


def harmonic_maps(resid: np.ndarray, r: np.ndarray, theta: np.ndarray, nbins: int = 64) -> tuple[np.ndarray, np.ndarray]:
    ny, nx = resid.shape
    m1 = np.zeros_like(resid) * np.nan
    m2 = np.zeros_like(resid) * np.nan
    rmax = r.max(); edges = np.linspace(0, rmax, nbins + 1)
    for i in range(nbins):
        m = (r >= edges[i]) & (r < edges[i+1]) & np.isfinite(resid)
        if not m.any():
            continue
        # Least squares for a cos(mθ)+b sin(mθ)
        th = theta[m]
        y = resid[m]
        c1 = np.column_stack([np.cos(th), np.sin(th)])
        c2 = np.column_stack([np.cos(2*th), np.sin(2*th)])
        try:
            a1, *_ = np.linalg.lstsq(c1, y, rcond=None)
            a2, *_ = np.linalg.lstsq(c2, y, rcond=None)
            amp1 = float(np.hypot(a1[0], a1[1]))
            amp2 = float(np.hypot(a2[0], a2[1]))
        except Exception:
            amp1 = np.nan; amp2 = np.nan
        m1[m] = amp1
        m2[m] = amp2
    return m1, m2


def overlay_contours(ax, ha_path: Path) -> None:
    try:
        img = fits.getdata(ha_path).astype(float)
        m = np.isfinite(img) & (img > 0)
        if m.any():
            lv = np.nanpercentile(img[m], [60, 80, 90, 97]).astype(float)
            lv = np.clip(lv, a_min=max(1e-30, float(lv[0])*1e-3), a_max=None)
            ax.contour(img, levels=lv, colors=['#99c', '#66a', '#338', '#115'], linewidths=[0.6,0.9,1.2,1.5])
    except Exception:
        return


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', required=True, help='Galaxy name (e.g., NGC3198)')
    ap.add_argument('--vel', type=Path, help='velocity field FITS (moment-1)',
                   default=None)
    ap.add_argument('--sigma-pix', type=float, default=1.0, help='optional Gaussian smoothing [pix]')
    args = ap.parse_args()

    gal = args.name
    if args.vel is None:
        args.vel = Path(f'data/vel/{gal}/velocity.fits')
    if not args.vel.exists():
        print('skip: velocity field not found:', args.vel)
        return 0

    v = fits.getdata(args.vel).astype(float)
    # Downsample very large maps to keep runtime reasonable
    ny, nx = v.shape
    maxdim = max(ny, nx)
    if maxdim > 1200:
        import scipy.ndimage as ndi
        scale = 800.0 / maxdim
        v = ndi.zoom(v, zoom=scale, order=1)
    if args.sigma_pix and args.sigma_pix > 0:
        ky = np.fft.fftfreq(v.shape[0])[:, None]
        kx = np.fft.fftfreq(v.shape[1])[None, :]
        k2 = (2*np.pi)**2 * (ky*ky + kx*kx)
        H = np.exp(-0.5 * (args.sigma_pix**2) * k2)
        Vk = np.fft.fft2(np.nan_to_num(v, nan=0.0))
        v = np.fft.ifft2(Vk * H).real

    resid, r, th, edges, med = ring_median_residual(v)
    m1, m2 = harmonic_maps(resid, r, th)

    out_dir = Path('server/public/reports')
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.8), constrained_layout=True)
    im0 = axs[0].imshow(resid, origin='lower', cmap='coolwarm',
                        vmin=-np.nanpercentile(np.abs(resid[np.isfinite(resid)]), 95),
                        vmax= np.nanpercentile(np.abs(resid[np.isfinite(resid)]), 95))
    axs[0].set_title('Residual (ring-median)'); axs[0].set_xticks([]); axs[0].set_yticks([])
    fig.colorbar(im0, ax=axs[0], fraction=0.046, pad=0.04)
    im1 = axs[1].imshow(m1, origin='lower', cmap='magma')
    axs[1].set_title('m=1 amplitude (warp/lopsided)'); axs[1].set_xticks([]); axs[1].set_yticks([])
    fig.colorbar(im1, ax=axs[1], fraction=0.046, pad=0.04)
    im2 = axs[2].imshow(m2, origin='lower', cmap='magma')
    axs[2].set_title('m=2 amplitude (bar/spiral)'); axs[2].set_xticks([]); axs[2].set_yticks([])
    fig.colorbar(im2, ax=axs[2], fraction=0.046, pad=0.04)
    # overlay Halpha if available
    ha = Path(f'data/halpha/{gal}/Halpha_SB.fits')
    if ha.exists():
        overlay_contours(axs[0], ha)
        overlay_contours(axs[1], ha)
        overlay_contours(axs[2], ha)
    out = out_dir / f'{gal.lower()}_noncircular_panels.png'
    fig.suptitle(f'{gal} — Non-circular diagnostics', fontsize=11)
    fig.savefig(out, dpi=140)
    plt.close(fig)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
