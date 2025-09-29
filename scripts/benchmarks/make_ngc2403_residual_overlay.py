#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from src.models.fdbl import irradiance_log_bias, circular_profile


def main() -> int:
    use_jp_font()
    ha = Path('data/halpha/NGC2403/Halpha_SB.fits')
    if not ha.exists():
        print('skip: no Halpha_SB.fits')
        return 0
    img = fits.getdata(ha).astype(float)
    m = np.isfinite(img) & (img > 0)
    v = np.zeros_like(img); v[m] = img[m]
    vf = v[np.isfinite(v) & (v > 0)]
    if vf.size == 0:
        print('warn: no positive finite Halpha pixels; skip overlay')
        return 0
    v = np.log10(np.clip(v, a_min=np.nanpercentile(vf, 5), a_max=np.nanpercentile(vf, 99.5)))
    # compute 2D approximate residual field magnitude |g_ULM|
    gx, gy = irradiance_log_bias(v, pix_kpc=0.2, strength=1.0, eps_kpc=0.8, pad_factor=1,
                                 beta_forward=0.0, forward_angle_deg=0.0)
    mag = np.hypot(gx, gy)
    # contour levels from Halpha
    fig, ax = plt.subplots(1,1, figsize=(6.0,4.8))
    im = ax.imshow(mag, origin='lower', cmap='magma')
    vf2 = v[np.isfinite(v)]
    if vf2.size >= 100:
        lv = np.nanpercentile(vf2, [60, 80, 90, 97]).astype(float)
        if np.all(np.isfinite(lv)) and (np.min(np.diff(lv)) > 0):
            ax.contour(v, levels=lv, colors=['#99c', '#66a', '#338', '#115'], linewidths=[0.6,0.9,1.2,1.5])
    ax.set_xticks([]); ax.set_yticks([])
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='|g_ULM| (arb.)')
    out = Path('server/public/reports/ngc2403_residual_ha.png')
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
