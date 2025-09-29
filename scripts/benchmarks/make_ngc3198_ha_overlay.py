#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font


def main() -> int:
    use_jp_font()
    base = Path('data/halpha/NGC3198/Halpha_SB.fits')
    if not base.exists():
        print('no Halpha_SB.fits; skip overlay')
        return 0
    img = fits.getdata(base).astype(float)
    # Normalize for contours
    m = np.isfinite(img) & (img > 0)
    if m.any():
        v = np.nanpercentile(img[m], [50, 75, 90, 97]).astype(float)
        # sanitize levels: finite, unique, strictly increasing, positive
        v = np.asarray(v, dtype=float)
        v = v[np.isfinite(v)]
        if v.size:
            v = np.clip(v, a_min=max(1e-30, float(np.nanmin(v))*1e-3), a_max=None)
            v = np.sort(np.unique(v))
        # fallback if non-increasing or too few levels
        if (v.size < 2) or (np.min(np.diff(v)) <= 0) or (np.nanmin(v) <= 0):
            vf = img[m]
            lo, hi = np.nanpercentile(vf, [60, 97]).astype(float)
            if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
                lo, hi = float(np.nanmin(vf)), float(np.nanmax(vf))
            # ensure strictly increasing with small safety margin
            eps = max(1e-30, abs(hi)*1e-6)
            v = np.array([lo + 0.0*eps, (lo + hi)/2.0, hi + eps], dtype=float)
    else:
        vmax = float(np.nanmax(img)) if np.isfinite(img).any() else 1.0
        v = np.array([0.1, 0.3, 0.5, 0.8]) * max(vmax, 1e-6)
    fig, ax = plt.subplots(1,1, figsize=(5.6, 4.2))
    cols = ['#88b', '#55a', '#227', '#004'][:len(v)]
    wts = [0.6,0.8,1.0,1.2][:len(v)]
    # Final safety: if levels somehow invalid, use linspace between finite min/max
    try:
        ax.contour(img, levels=v, colors=cols, linewidths=wts)
    except Exception as e:
        vf = img[m] if m.any() else img[np.isfinite(img)]
        if vf.size >= 2:
            lo, hi = float(np.nanmin(vf)), float(np.nanmax(vf))
            lv = np.linspace(max(1e-30, lo), hi, num=min(4, max(2, len(v))))
            ax.contour(img, levels=np.sort(np.unique(lv)), colors=cols, linewidths=wts)
        else:
            print('warn: failed to draw Halpha contours:', e)
    ax.set_title('NGC 3198 — Hα 等高線（基準化、重ね用）')
    ax.set_xticks([]); ax.set_yticks([])
    out = Path('server/public/reports/ngc3198_ha_contours.png')
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
