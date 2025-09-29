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
    base = Path('data/halpha/NGC2403/Halpha_SB.fits')
    if not base.exists():
        print('no Halpha_SB.fits; skip overlay')
        return 0
    img = fits.getdata(base).astype(float)
    m = np.isfinite(img) & (img > 0)
    v = np.zeros_like(img); v[m] = img[m]
    vf = v[np.isfinite(v) & (v > 0)]
    if vf.size == 0:
        print('warn: no positive finite Halpha pixels; skip')
        return 0
    v = np.log10(np.clip(v, a_min=np.nanpercentile(vf, 5), a_max=np.nanpercentile(vf, 99.5)))
    fig, ax = plt.subplots(1,1, figsize=(5.4,4.2))
    im = ax.imshow(v, origin='lower', cmap='gist_heat')
    vf2 = v[np.isfinite(v)]
    if vf2.size >= 100:
        lv = np.nanpercentile(vf2, [60, 80, 90, 97]).astype(float)
        if np.all(np.isfinite(lv)) and (np.min(np.diff(lv)) > 0):
            ax.contour(v, levels=lv, colors=['#9cf','#69a','#347','#114'], linewidths=[0.6,0.9,1.2,1.5])
    ax.set_title('NGC 2403 — Hα 等高線')
    ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='log10 I_Hα (norm)')
    out = Path('server/public/reports/ngc2403_ha_contours.png')
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
