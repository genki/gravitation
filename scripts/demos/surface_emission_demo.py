#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font

from fdb.grids import make_thin_disk
from fdb.fft_eval import phi_eff_fft_iso_mu, phi_eff_fft_l2_mu
from fdb.surface_emission import extract_isosurface, line_integral_us, lambda_at_points


def main() -> int:
    use_jp_font()
    out_dir = Path('server/public/reports'); out_dir.mkdir(parents=True, exist_ok=True)
    img_dir = Path('assets/figures/surface'); img_dir.mkdir(parents=True, exist_ok=True)
    # Build a mock galaxy disk density and a proxy ne field ~ rho
    grid = make_thin_disk(R=20.0, h=4.0, rho0=1.0, spacing=1.0)
    rho = grid.rho.astype(float)
    ne = rho.copy()  # proxy
    level = 0.5  # ω_cut* 等価のしきいとして近似
    surf = extract_isosurface(ne, level, spacing=grid.spacing)
    # Compute u_s(s) by line integral into the disk; shared L_d
    Ld = 5.0
    us = line_integral_us(surf.centers, surf.normals, rho, origin=grid.origin, spacing=grid.spacing, Ld=Ld)
    c = 2.99792458e5  # km/s for scale (arbitrary unit consistency)
    alpha_esc = 0.6
    J = alpha_esc * c * us / 4.0
    # Evaluate Λ(x) at mid-plane points along x-axis
    z0 = (grid.rho.shape[0]//2 + 0.5) * grid.spacing[2]
    y0 = (grid.rho.shape[1]//2 + 0.5) * grid.spacing[1]
    xs = np.linspace(2.0, 30.0, 60)
    pts = np.stack([xs, np.full_like(xs, y0), np.full_like(xs, z0)], axis=1)
    Lam = lambda_at_points(surf.centers, surf.normals, surf.areas, J, pts)
    # Compare with volumetric h-only potential gradient via FFT (μ0≈1)
    phi_iso = phi_eff_fft_iso_mu(rho, grid.spacing, eps=1e-3, eps_mu=1.0, k0=0.2, m=2.0)
    phi_l2  = phi_eff_fft_l2_mu(rho, np.zeros_like(rho)+0.35, grid.spacing, (0,0,1), eps=1e-3, eps_mu=1.0, k0=0.2, m=2.0)
    # Make a simple comparison plot of Λ (scaled) vs dΦ/dx proxy
    dz, dy, dx = grid.spacing[2], grid.spacing[1], grid.spacing[0]
    zc = grid.rho.shape[0]//2; yc = grid.rho.shape[1]//2
    dphidx = (phi_iso[zc,yc,2:] - phi_iso[zc,yc,:-2])/(2*dx)
    xg = np.arange(1, phi_iso.shape[2]-1) * dx
    fig, ax = plt.subplots(1,1, figsize=(6,3.5))
    ax.plot(xs, Lam / np.max(np.abs(Lam)), label='Λ(surface) [scaled]')
    ax.plot(xg, -dphidx/np.max(np.abs(dphidx)), label='−∂Φ_iso/∂x [scaled]')
    ax.set_xlabel('x [arb]'); ax.set_ylabel('scaled')
    ax.legend(frameon=False, fontsize=9); ax.grid(True, ls=':', alpha=0.4)
    p = img_dir / 'surface_vs_volume.png'
    fig.tight_layout(); fig.savefig(p, dpi=140); plt.close(fig)
    # HTML report
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Surface-Emission FDB Demo</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">ホーム</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>界面放射（Σ）モデル: デモ</h1>',
        '<p>等値面Σを抽出し、表面流束J_outからΛ(x)を評価。体積版(ρ·Â)との比較の最小デモ。</p>',
        f'<p><img src="../{p}" style="max-width:100%"></p>',
        '</main></body></html>'
    ]
    (out_dir / 'surface_emission_demo.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out_dir / 'surface_emission_demo.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
