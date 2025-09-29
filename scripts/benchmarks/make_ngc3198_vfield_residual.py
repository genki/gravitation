#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import argparse
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font


def gaussian_fft(img: np.ndarray, sigma_pix: float) -> np.ndarray:
    if sigma_pix <= 0: return img
    ny, nx = img.shape
    ky = np.fft.fftfreq(ny)[:, None]
    kx = np.fft.fftfreq(nx)[None, :]
    k2 = (2*np.pi)**2 * (ky*ky + kx*kx)
    H = np.exp(-0.5 * (sigma_pix**2) * k2)
    Ik = np.fft.fft2(np.nan_to_num(img, nan=0.0))
    out = np.fft.ifft2(Ik * H).real
    return out


def ring_median_residual(v: np.ndarray, nbins: int = 60) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ny, nx = v.shape
    yy, xx = np.indices((ny, nx))
    cy, cx = (ny - 1) / 2.0, (nx - 1) / 2.0
    r = np.hypot(xx - cx, yy - cy)
    rmax = r.max(); edges = np.linspace(0, rmax, nbins + 1)
    med = np.zeros_like(v) + np.nan
    for i in range(nbins):
        m = (r >= edges[i]) & (r < edges[i+1]) & np.isfinite(v)
        if not m.any():
            continue
        rv = np.nanmedian(v[m])
        med[m] = rv
    resid = v - med
    return resid, r, edges


def main() -> int:
    use_jp_font()
    ap = argparse.ArgumentParser(description='Velocity-field residual (ring-median) over Halpha contours')
    ap.add_argument('--vel', type=Path, default=Path('data/vel/NGC3198/velocity.fits'))
    ap.add_argument('--sigma-pix', type=float, default=0.0, help='gaussian sigma [pix] to smooth velocity')
    args = ap.parse_args()
    if not args.vel.exists():
        print('skip: velocity field not found')
        return 0
    v = fits.getdata(args.vel).astype(float)
    if args.sigma_pix > 0:
        v = gaussian_fft(v, sigma_pix=float(args.sigma_pix))
    resid, r, edges = ring_median_residual(v)
    # Halpha contours if present
    ha = Path('data/halpha/NGC3198/Halpha_SB.fits')
    ha_img = None
    if ha.exists():
        ha_img = fits.getdata(ha).astype(float)
    # plot
    fig, ax = plt.subplots(1,1, figsize=(6.2,4.6))
    im = ax.imshow(resid, origin='lower', cmap='coolwarm', vmin=-np.nanpercentile(abs(resid[np.isfinite(resid)]), 95), vmax=np.nanpercentile(abs(resid[np.isfinite(resid)]), 95))
    if ha_img is not None:
        m = np.isfinite(ha_img) & (ha_img > 0)
        if m.any():
            lv = np.nanpercentile(ha_img[m], [60, 80, 90, 97]).astype(float)
            lv = np.sort(np.unique(np.clip(lv, a_min=max(1e-30, float(lv[0])*1e-3), a_max=None)))
            if lv.size < 2:
                lv = np.array([float(np.nanpercentile(ha_img[m], 70)), float(np.nanpercentile(ha_img[m], 95))])
            ax.contour(ha_img, levels=lv, colors=['#99c', '#66a', '#338', '#115'][:len(lv)], linewidths=[0.6,0.9,1.2,1.5][:len(lv)])
    ax.set_title('NGC 3198 — 面内残差（リング中央値差し引き）× Hα 等高線')
    ax.set_xticks([]); ax.set_yticks([])
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('V_residual (arb.)')
    out = Path('server/public/reports/ngc3198_vfield_residual_ha.png')
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
