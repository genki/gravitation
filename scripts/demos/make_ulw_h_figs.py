#!/usr/bin/env python3
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font

from fdb.grids import make_uniform_sphere, make_thin_disk, make_finite_rod
from fdb.fft_eval import phi_eff_fft_iso, phi_eff_fft_l2


def mid_slice(arr: np.ndarray, axis: int = 0) -> np.ndarray:
    idx = [slice(None)]*3
    idx[axis] = arr.shape[axis]//2
    return arr[tuple(idx)]


def rotation_curve(phi: np.ndarray, spacing: tuple[float,float,float]) -> tuple[np.ndarray,np.ndarray]:
    """Compute v_c(R) along x-axis in mid-plane using finite-difference of Φ.
    Returns (R, v_c). Units are arbitrary but consistent.
    """
    nz, ny, nx = phi.shape
    dx = spacing[0]
    zc = nz//2; yc = ny//2
    # sample along +x
    xs = np.arange(1, nx-1)
    # g_R = dΦ/dx (since R=x on axis). a_R = -dΦ/dR
    dphidx = (phi[zc,yc,2:] - phi[zc,yc,:-2])/(2*dx)
    gR = -dphidx  # acceleration toward center is negative gradient
    R = (xs[1:-1] - xs.mean()*0 + 0.0) * dx
    v2 = np.maximum(gR[1:-1] * R, 0.0)
    return R, np.sqrt(v2)


def make_panels(tag: str, rho, a2, phi_iso, phi_tot, spacing, outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    # images: rho slice, a2 slice, phi_tot slice
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
    im0 = axes[0].imshow(mid_slice(rho, axis=0), cmap='inferno', origin='lower')
    axes[0].set_title('ρ (mid-slice)')
    plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)
    im1 = axes[1].imshow(mid_slice(a2, axis=0), cmap='coolwarm', origin='lower', vmin=-np.max(np.abs(a2)), vmax=np.max(np.abs(a2)))
    axes[1].set_title('a₂ (mid-slice)')
    plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)
    im2 = axes[2].imshow(mid_slice(phi_tot, axis=0), cmap='viridis', origin='lower')
    axes[2].set_title('Φ_eff (h‑only)')
    plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)
    for ax in axes: ax.set_xticks([]); ax.set_yticks([])
    fig.suptitle(f'{tag}: tri‑panel (ρ, a₂, Φ_eff)', fontsize=11)
    p_png = outdir / f'ulw_h_tripanel_{tag}.png'
    fig.tight_layout()
    fig.savefig(p_png, dpi=140)
    plt.close(fig)

    # rotation curves
    R, v_iso = rotation_curve(phi_iso, spacing)
    _, v_tot = rotation_curve(phi_tot, spacing)
    dv = np.sqrt(np.maximum(v_tot**2 - v_iso**2, 0.0))
    fig2, ax = plt.subplots(1,1, figsize=(5.2,3.4))
    ax.plot(R, v_iso, label='v_N (等方)', lw=1.8)
    ax.plot(R, v_tot, label='v_total (h‑only)', lw=1.8)
    ax.plot(R, dv, label='δv_FDB (異方+μ0≈1)', lw=1.5, ls='--')
    ax.set_xlabel('R [arb]'); ax.set_ylabel('v [arb]'); ax.grid(True, ls=':', alpha=0.4)
    ax.legend(frameon=False, fontsize=9)
    p2_png = outdir / f'ulw_h_rc_{tag}.png'
    fig2.tight_layout(); fig2.savefig(p2_png, dpi=140)
    plt.close(fig2)
    return p_png, p2_png


def main() -> int:
    use_jp_font()
    out_img = Path('assets/figures/ulw_h')
    out_html = Path('server/public/reports/ulw_h_demos.html')
    out_img.mkdir(parents=True, exist_ok=True)

    cases = []
    # sphere
    grid = make_uniform_sphere(R=10.0, rho0=1.0, spacing=1.0)
    rho = grid.rho.astype(float)
    a2 = np.zeros_like(rho)
    phi0 = phi_eff_fft_iso(rho, grid.spacing, eps=1e-3)
    phi2 = phi_eff_fft_l2(rho, a2, grid.spacing, n_hat=(0,0,1), eps=1e-3)
    phi = phi0 + phi2
    cases.append(('sphere', rho, a2, phi0, phi, grid.spacing))

    # thin disk
    grid = make_thin_disk(R=16.0, h=4.0, rho0=1.0, spacing=1.0)
    rho = grid.rho.astype(float)
    a2 = np.zeros_like(rho); a2[rho>0] = 0.35  # constant anisotropy inside
    phi0 = phi_eff_fft_iso(rho, grid.spacing, eps=1e-3)
    phi2 = phi_eff_fft_l2(rho, a2, grid.spacing, n_hat=(0,0,1), eps=1e-3)
    phi = phi0 + phi2
    cases.append(('disk', rho, a2, phi0, phi, grid.spacing))

    # bar (finite rod along z)
    grid = make_finite_rod(L=28.0, radius=4.0, rho0=1.0, spacing=1.0)
    rho = grid.rho.astype(float)
    a2 = np.zeros_like(rho); a2[rho>0] = 0.5
    phi0 = phi_eff_fft_iso(rho, grid.spacing, eps=1e-3)
    phi2 = phi_eff_fft_l2(rho, a2, grid.spacing, n_hat=(0,0,1), eps=1e-3)
    phi = phi0 + phi2
    cases.append(('bar', rho, a2, phi0, phi, grid.spacing))

    panel_paths = []
    for tag, rho, a2, phi0, phi, sp in cases:
        p1, p2 = make_panels(tag, rho, a2, phi0, phi, sp, out_img)
        panel_paths.append((tag, p1, p2))

    # HTML report
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>ULW‑l/h Demos</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">ホーム</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>ULW‑l/h デモ（h‑only）</h1>',
        '<p>三面図: ρ, a₂, Φ_eff（h‑only）。回転曲線分解: v_c^2 = v_N^2 (等方) + δv_FDB^2 (異方 + μ0≈1)。</p>'
    ]
    for tag, p1, p2 in panel_paths:
        html.append(f'<h2>{tag}</h2>')
        html.append(f'<p><img src="../{p1}" style="max-width:100%"></p>')
        html.append(f'<p><img src="../{p2}" style="max-width:100%"></p>')
    html.append('</main></body></html>')
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out_html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
