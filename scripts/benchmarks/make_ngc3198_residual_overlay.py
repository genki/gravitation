#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from src.models.fdbl import irradiance_log_bias


def main() -> int:
    use_jp_font()
    ha = Path('data/halpha/NGC3198/Halpha_SB.fits')
    if not ha.exists():
        print('skip: no Halpha_SB.fits')
        return 0
    img = fits.getdata(ha).astype(float)
    # normalize input emissivity proxy (non-negative)
    j = np.nan_to_num(img, nan=0.0, posinf=0.0, neginf=0.0)
    if j.max() > 0:
        j = j / j.max()
    # compute 2D approximate residual field magnitude |g_ULM|
    pix_kpc = 0.2  # bench既定のpix
    gx, gy = irradiance_log_bias(j, pix_kpc=pix_kpc, strength=1.0, eps_kpc=0.8, pad_factor=1,
                                 beta_forward=0.0, forward_angle_deg=0.0)
    gmag = np.sqrt(gx*gx + gy*gy)
    # contour levels from Halpha
    m = np.isfinite(img) & (img > 0)
    if m.any():
        v = np.nanpercentile(img[m], [60, 80, 90, 97]).astype(float)
        v = np.asarray(v, dtype=float)
        v = v[np.isfinite(v)]
        if v.size:
            v = np.clip(v, a_min=max(1e-30, float(np.nanmin(v))*1e-3), a_max=None)
            v = np.sort(np.unique(v))
        if (v.size < 2) or (np.min(np.diff(v)) <= 0) or (np.nanmin(v) <= 0):
            vf = img[m]
            lo, hi = np.nanpercentile(vf, [60, 97]).astype(float)
            if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
                lo, hi = float(np.nanmin(vf)), float(np.nanmax(vf))
            eps = max(1e-30, abs(hi)*1e-6)
            v = np.array([lo, (lo + hi)/2.0, hi + eps], dtype=float)
    else:
        vmax = float(np.nanmax(img)) if np.isfinite(img).any() else 1.0
        v = np.array([0.2, 0.4, 0.6, 0.8]) * max(vmax, 1e-6)
    # figure
    fig, ax = plt.subplots(1,1, figsize=(6.2,4.6))
    im = ax.imshow(gmag, origin='lower', cmap='magma')
    try:
        cs = ax.contour(img, levels=v, colors=['#99c', '#66a', '#338', '#115'], linewidths=[0.6,0.9,1.2,1.5])
    except Exception as e:
        vf = img[m] if m.any() else img[np.isfinite(img)]
        if vf.size >= 2:
            lo, hi = float(np.nanmin(vf)), float(np.nanmax(vf))
            lv = np.linspace(max(1e-30, lo), hi, num=min(4, max(2, len(v))))
            cs = ax.contour(img, levels=np.sort(np.unique(lv)), colors=['#99c', '#66a', '#338', '#115'], linewidths=[0.6,0.9,1.2,1.5])
        else:
            print('warn: failed to draw residual Halpha contours:', e)
    ax.set_title('NGC 3198 — 残差ヒートマップ（|g_ULM|）× Hα 等高線')
    ax.set_xticks([]); ax.set_yticks([])
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('|g_ULM| (arb.)')
    out = Path('server/public/reports/ngc3198_residual_ha.png')
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
