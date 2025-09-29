#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font

from src.fdb.grids import make_thin_disk
from src.fdb.composite import build_layers
from src.fdb.fft_eval import phi_eff_fft_iso_mu


def mid_slice(a: np.ndarray) -> np.ndarray:
    return a[a.shape[0]//2, :, :]


def rotation_curve(phi: np.ndarray, spacing):
    nz, ny, nx = phi.shape
    dx = spacing[0]
    zc, yc = nz//2, ny//2
    dphidx = (phi[zc,yc,2:] - phi[zc,yc,:-2])/(2*dx)
    x = np.arange(1, nx-1) * dx
    R = x[1:-1]
    gR = -dphidx[1:-1]
    return R, np.sqrt(np.maximum(gR*R, 0.0))


def main() -> int:
    use_jp_font()
    out_html = Path('server/public/reports/two_layer_demo.html'); out_html.parent.mkdir(parents=True, exist_ok=True)
    out_img = Path('assets/figures/twolayer'); out_img.mkdir(parents=True, exist_ok=True)
    # mock fields
    disk = make_thin_disk(R=20.0, h=4.0, rho0=1.0, spacing=1.0)
    rho_star = 0.6 * disk.rho
    rho_gas  = 0.4 * disk.rho
    proxy    = rho_gas  # use gas as n_e proxy for demo
    rho_iso, S, rho_eff, meta = build_layers(rho_star, rho_gas, proxy, disk.spacing, gas_scale=1.33, alpha_esc=0.5, ell_star=5.0, omega_star=0.4, smooth_sigma=1.0)
    # potentials (μ0≈1)
    phi_iso = phi_eff_fft_iso_mu(rho_iso, disk.spacing, eps=1e-3, eps_mu=1.0, k0=0.2, m=2.0)
    phi_eff = phi_eff_fft_iso_mu(rho_eff, disk.spacing, eps=1e-3, eps_mu=1.0, k0=0.2, m=2.0)
    # slices
    fig, axes = plt.subplots(1,3, figsize=(10,3.2))
    for ax, img, ttl in zip(axes, [mid_slice(rho_iso), mid_slice(S), mid_slice(rho_eff)], ['ρ_iso (stars+gas)','S (surface source)','ρ_eff = ρ_iso + α S']):
        im = ax.imshow(img, origin='lower', cmap='viridis')
        ax.set_title(ttl); ax.set_xticks([]); ax.set_yticks([])
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    p1 = out_img / 'two_layers_maps.png'
    fig.tight_layout(); fig.savefig(p1, dpi=140); plt.close(fig)
    # rotation curve decomposition
    R, v_iso = rotation_curve(phi_iso, disk.spacing)
    _, v_eff = rotation_curve(phi_eff, disk.spacing)
    dv = np.sqrt(np.maximum(v_eff**2 - v_iso**2, 0.0))
    fig2, ax = plt.subplots(1,1, figsize=(5.4,3.4))
    ax.plot(R, v_iso, label='等方: stars+gas', lw=1.8)
    ax.plot(R, v_eff, label='合成: 等方 + 追加', lw=1.8)
    ax.plot(R, dv, label='追加(FDB, surface)', lw=1.5, ls='--')
    ax.set_xlabel('R'); ax.set_ylabel('v'); ax.grid(True, ls=':', alpha=0.4); ax.legend(frameon=False, fontsize=9)
    p2 = out_img / 'two_layers_rc.png'
    fig2.tight_layout(); fig2.savefig(p2, dpi=140); plt.close(fig2)
    # HTML
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Two-Layer FDB Demo</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">ホーム</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>等方（GR等価）＋追加（界面）— 2層デモ</h1>',
        f'<p><img src="../{p1}" style="max-width:100%"></p>',
        f'<p><img src="../{p2}" style="max-width:100%"></p>',
        '</main></body></html>'
    ]
    out_html.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out_html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
