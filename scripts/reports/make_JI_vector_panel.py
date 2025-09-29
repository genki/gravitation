#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from astropy.io import fits

from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_vector_from_map
from scripts.fit_sparc_fdbl import read_sparc_massmodels, make_axisymmetric_image


def load_ha_or_proxy(name: str):
    p = Path(f'data/halpha/{name}/Halpha_SB.fits')
    if p.exists():
        img = fits.getdata(p).astype(float)
        hdr = fits.getheader(p)
        pix = float(hdr.get('PIXSCALE', 0.305)) / 206265.0 * 1.0
        if not np.isfinite(pix) or pix <= 0:
            pix = 0.2
        return img, pix
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    return make_axisymmetric_image(rc.R, rc.SBdisk, pix_kpc=0.2, size=256), 0.2


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='Plot J_I vector-derived apparent acceleration fields (beta vs isotropic)')
    ap.add_argument('--name', required=True)
    ap.add_argument('--beta', type=float, default=0.3)
    ap.add_argument('--s', type=float, default=0.5)
    ap.add_argument('--sgk', type=float, default=0.6)
    ap.add_argument('--max-size', type=int, default=192)
    args = ap.parse_args()

    nm = args.name
    img, pix = load_ha_or_proxy(nm)
    H, W = img.shape[:2]
    fac = int(np.ceil(max(H, W) / float(args.max_size))) if max(H, W) > args.max_size else 1
    if fac > 1:
        hh = (H // fac) * fac; ww = (W // fac) * fac
        img = img[:hh, :ww].reshape(hh//fac, fac, ww//fac, fac).mean(axis=(1,3))
        pix *= fac
    k_grid = np.linspace(0.02, 1.2, 16)
    phi_k = np.exp(-(k_grid/args.sgk)**2)
    # beta vs isotropic
    ax1, ay1 = info_bias_vector_from_map(img, pix, k_grid, phi_k, EtaParams(beta=args.beta, s_kpc=args.s))
    ax0, ay0 = info_bias_vector_from_map(img, pix, k_grid, phi_k, EtaParams(beta=0.0, s_kpc=args.s))
    # figure
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 4.2), constrained_layout=True)
    for j,(ax,ay,title,axp) in enumerate(((ax0,ay0,'β=0 (等方)',axs[0]), (ax1,ay1,f'β={args.beta} (前方化)',axs[1]))):
        mag = np.hypot(ax, ay); im = axp.imshow(mag, origin='lower', cmap='magma')
        axp.set_title(f'{nm} — {title}')
        axp.set_xticks([]); axp.set_yticks([])
        # downsample quiver grid
        step = max(1, int(max(mag.shape)/48))
        yy, xx = np.mgrid[0:mag.shape[0]:step, 0:mag.shape[1]:step]
        axp.quiver(xx, yy, ax[::step,::step], ay[::step,::step], color='w', scale=50, width=0.002, alpha=0.7)
        plt.colorbar(im, ax=axp, fraction=0.046, pad=0.04, label='|a_IF| (arb)')
    png = outdir / f'{nm.lower()}_JI_vector_panel.png'
    fig.savefig(png, dpi=140); plt.close(fig)
    # HTML
    html = outdir / f'{nm.lower()}_JI_vector_panel.html'
    parts = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{nm}: J_I ベクトル場（β比較）</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        f'<main class="wrap"><h1>{nm}: 情報流 J_I 起因の見かけ加速度（β=0 vs β>0）</h1>',
        f'<div class=card><img src="{png.name}" style="max-width:100%"></div>',
        '<div class=card><small>構成: k格子16点, φ_k=exp[−(k/σ_k)^2], σ_k=指定値。ベクトルは潜在ポテンシャルの勾配から導出（1/|k|カーネル）。</small></div>',
        '</main></body></html>'
    ]
    html.write_text('\n'.join(parts), encoding='utf-8')
    print('wrote', html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

