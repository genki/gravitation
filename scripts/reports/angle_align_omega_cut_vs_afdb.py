#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import ndimage as ndi

from scripts.utils.mpl_fonts import use_jp_font
from src.fdb.a_from_info import info_bias_vector_from_map
from theory.info_decoherence import EtaParams


def em_to_ne_cm3(EM_pc_cm6: np.ndarray, L_pc: float) -> np.ndarray:
    L = max(float(L_pc), 1.0)
    return np.sqrt(np.maximum(EM_pc_cm6, 0.0) / L)


def plasma_freq_rad_s(ne_cm3: np.ndarray) -> np.ndarray:
    return 5.64e4 * np.sqrt(np.maximum(ne_cm3, 0.0))


def main() -> int:
    use_jp_font()
    ap = argparse.ArgumentParser(description='Angle alignment between ∇ω_cut and a_FDB (info-flow)')
    ap.add_argument('--name', required=True)
    ap.add_argument('--L-pc', type=float, default=100.0)
    args = ap.parse_args()
    g = args.name.strip()
    # Load EM -> omega_cut
    em_p = Path(f'data/halpha/{g}/EM_pc_cm6.fits')
    if not em_p.exists():
        print('missing', em_p)
        return 0
    EM = fits.getdata(em_p).astype(float)
    if max(EM.shape) > 1200:
        EM = ndi.zoom(EM, zoom=800.0/max(EM.shape), order=1)
    ne = em_to_ne_cm3(EM, args.L_pc)
    wcut = plasma_freq_rad_s(ne)
    # Compute a_FDB vector from EM map via info-flow model
    pix_kpc = 0.2  # proxy
    k_grid = np.linspace(0.02, 1.0, 20); phi_k = np.exp(-(k_grid/0.6)**2)
    ax, ay = info_bias_vector_from_map(EM, pix_kpc=pix_kpc, k_grid=k_grid, phi_k=phi_k, eta_params=EtaParams(beta=0.3, s_kpc=0.5))
    # ∇ω_cut
    gy, gx = np.gradient(wcut, pix_kpc)
    # unit vectors
    amag = np.hypot(ax, ay); am = (amag > np.nanpercentile(amag, 50))  # focus on stronger pixels
    axu = np.divide(ax, amag, out=np.zeros_like(ax), where=amag>0)
    ayu = np.divide(ay, amag, out=np.zeros_like(ay), where=amag>0)
    gmag = np.hypot(gx, gy)
    gxu = np.divide(gx, gmag, out=np.zeros_like(gx), where=gmag>0)
    gyu = np.divide(gy, gmag, out=np.zeros_like(gy), where=gmag>0)
    # angles between vectors
    dot = gxu*axu + gyu*ayu
    dot = np.clip(dot, -1.0, 1.0)
    ang = np.arccos(dot)  # radians
    m = np.isfinite(ang) & am
    angv = ang[m]
    if angv.size < 10:
        print('too few points')
        return 0
    mean_abs_deg = float(np.degrees(np.nanmean(np.abs(angv))))
    # Rayleigh test approx (for angles centered near 0): mean resultant length R
    R = float(np.hypot(np.nanmean(np.cos(angv)), np.nanmean(np.sin(angv))))
    n = int(np.sum(m))
    z = (n * (R ** 2))
    # p-value approx (Berens 2009)
    p = np.exp(np.sqrt(1 + 4*n + 4*(n**2 - (n*R)**2)) - (1 + 2*n))
    # Plots
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    # Histogram
    fig, axp = plt.subplots(1,1, figsize=(5.2,3.6))
    axp.hist(np.degrees(angv), bins=36, range=(0,180), color='#4477aa', alpha=0.8)
    axp.set_xlabel('angle(∇ω_cut, a_FDB) [deg]'); axp.set_ylabel('count')
    axp.set_title(f'mean|θ|≈{mean_abs_deg:.1f}°, R≈{R:.2f}, p≈{p:.1e} (n={n})')
    png = outdir / f'{g.lower()}_angle_align_hist.png'
    fig.tight_layout(); fig.savefig(png, dpi=140); plt.close(fig)
    # HTML
    html = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            f'<title>{g}: 角度整合（∇ω_cut vs a_FDB）</title><link rel="stylesheet" href="../styles.css"></head><body>',
            '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
            f'<main class="wrap"><h1>{g}: ∇ω_cut と a_FDB の角度整合</h1>',
            f'<div class=card><p>mean|θ|≈{mean_abs_deg:.1f}°, R≈{R:.2f}, p≈{p:.1e}, n={n}</p>'
            '<p><small>注: a_FDB はEM由来の情報流モデルから算出。勾配・加速度ベクトルは中央値以上の強度画素に限定。</small></p></div>',
            f'<div class=card><img src="{png.name}" style="max-width:100%"></div>',
            '</main></body></html>']
    (outdir / f'{g.lower()}_angle_align.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote', outdir / f'{g.lower()}_angle_align.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

