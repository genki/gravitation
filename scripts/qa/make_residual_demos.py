#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from fdb.grids import make_thin_disk, make_finite_rod
from fdb.fft_eval import phi_eff_fft_iso_mu, phi_eff_fft_l2_mu


def residual_maps(tag: str, grid, a2_val: float, eps_mu: float, k0: float, m: float, out: Path):
    rho = grid.rho.astype(float)
    phi_iso = phi_eff_fft_iso_mu(rho, grid.spacing, eps=1e-3, eps_mu=eps_mu, k0=k0, m=m)
    phi_l2  = phi_eff_fft_l2_mu(rho, np.zeros_like(rho)+a2_val, grid.spacing, (0,0,1), eps=1e-3, eps_mu=eps_mu, k0=k0, m=m)
    phi_tot = phi_iso + phi_l2
    # mid-plane residual acceleration magnitude |∇(Φ_tot-Φ_iso)|
    def grad(phi):
        dz, dy, dx = grid.spacing[2], grid.spacing[1], grid.spacing[0]
        gx = (np.roll(phi, -1, axis=2) - np.roll(phi, 1, axis=2)) / (2*dx)
        gy = (np.roll(phi, -1, axis=1) - np.roll(phi, 1, axis=1)) / (2*dy)
        gz = (np.roll(phi, -1, axis=0) - np.roll(phi, 1, axis=0)) / (2*dz)
        return gx, gy, gz
    gx0, gy0, gz0 = grad(phi_iso)
    gx , gy , gz  = grad(phi_tot)
    dgm = np.sqrt((gx-gx0)**2 + (gy-gy0)**2 + (gz-gz0)**2)
    sl = dgm[dgm.shape[0]//2, :, :]  # mid z
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1,1, figsize=(4.6,4.0))
    im = ax.imshow(sl, origin='lower', cmap='magma')
    ax.set_title(f'{tag}: residual |Δg| (h‑only)')
    ax.set_xticks([]); ax.set_yticks([])
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    p = out / f'residual_{tag}.png'
    fig.tight_layout(); fig.savefig(p, dpi=140); plt.close(fig)
    return p


def main() -> int:
    use_jp_font()
    out_img = Path('assets/figures/residuals')
    out_html = Path('server/public/reports/residual_demos.html')
    eps_mu, k0, m = 1.0, 0.2, 2.0
    a2 = 0.35
    pths = []
    disk = make_thin_disk(R=20.0, h=4.0, rho0=1.0, spacing=1.0)
    pths.append(('disk', residual_maps('disk', disk, a2, eps_mu, k0, m, out_img)))
    rod  = make_finite_rod(L=30.0, radius=3.0, rho0=1.0, spacing=1.0)
    pths.append(('bar', residual_maps('bar', rod, a2, eps_mu, k0, m, out_img)))
    # HTML
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Residual Demos</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">ホーム</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>残差ヒートマップ（h‑only, デモ）</h1><p>棒軸・面内の残差 |Δg| 可視化。異方 a₂ による「中心向き」追加成分の空間構造を表示。</p>'
    ]
    for tag, p in pths:
        html.append(f'<h2>{tag}</h2><p><img src="../{p}" style="max-width:100%"></p>')
    html.append('</main></body></html>')
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out_html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
