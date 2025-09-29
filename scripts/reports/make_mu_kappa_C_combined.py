#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from astropy.io import fits

from scripts.fit_sparc_fdbl import read_sparc_massmodels
from scripts.compare_fit_multi import to_accel, chi2
from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_profile_from_map


def with_error_floor(R, Vobs, eV):
    Vobs = np.asarray(Vobs, float); eV = np.asarray(eV, float)
    floor = np.clip(0.03*np.abs(Vobs), 3.0, 7.0)
    eVe = np.sqrt(np.maximum(eV,1e-6)**2 + floor**2)
    return to_accel(R, Vobs, eVe)


def load_ha_or_proxy(name: str):
    p = Path(f'data/halpha/{name}/Halpha_SB.fits')
    if p.exists():
        img = fits.getdata(p).astype(float)
        hdr = fits.getheader(p)
        pix = float(hdr.get('PIXSCALE', 0.305)) / 206265.0 * 1.0
        if not np.isfinite(pix) or pix <= 0:
            pix = 0.2
        if max(img.shape) > 1200:
            import scipy.ndimage as ndi
            img = ndi.zoom(img, zoom=800.0/max(img.shape), order=1)
        return img, pix
    # fallback: symmetric proxy from SBdisk
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    from scripts.fit_sparc_fdbl import make_axisymmetric_image
    return make_axisymmetric_image(rc.R, rc.SBdisk, pix_kpc=0.2, size=256), 0.2


def mu_kappa_profile(name: str):
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    R = rc.R; g_gas = (1.33*(rc.Vgas*rc.Vgas))/np.maximum(R,1e-6); g_star0 = (rc.Vdisk*rc.Vdisk+rc.Vbul*rc.Vbul)/np.maximum(R,1e-6)
    g_obs, eg = with_error_floor(R, rc.Vobs, rc.eV)
    img, pix = load_ha_or_proxy(name)
    k_grid = np.linspace(0.02, 1.0, 20); phi_k = np.exp(-(k_grid/0.6)**2)
    g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k, eta_params=EtaParams(beta=0.3, s_kpc=0.5))
    m = np.isfinite(g_obs)&np.isfinite(eg)&np.isfinite(g_gas)&np.isfinite(g_star0)&np.isfinite(g_if)
    # LS solution for start
    def fit():
        mb = m
        w = 1.0/np.maximum(eg[mb],1e-6)
        X1 = g_star0[mb]; X2 = g_if[mb]
        Y  = g_obs[mb] - g_gas[mb]
        S11 = float(np.nansum(w*X1*X1)); S22 = float(np.nansum(w*X2*X2)); S12 = float(np.nansum(w*X1*X2))
        b1  = float(np.nansum(w*X1*Y));   b2  = float(np.nansum(w*X2*Y))
        det = S11*S22 - S12*S12
        if det <= 0: return 0.8, 1.0
        mu = (b1*S22 - b2*S12) / det
        k  = (S11*b2 - S12*b1) / det
        return float(max(mu,0.0)), float(max(k,0.0))
    mu0, k0 = fit()
    mu_grid = np.linspace(max(0, mu0-0.6), mu0+0.6, 49)
    kap_grid= np.linspace(max(0, k0-2.0), k0+2.0, 49)
    Z = np.empty((len(mu_grid), len(kap_grid)))
    for i, mu in enumerate(mu_grid):
        g1 = g_gas + mu*g_star0
        for j, k in enumerate(kap_grid):
            gmod = g1 + k*g_if
            Z[i,j] = chi2(g_obs[m], eg[m], gmod[m])
    dchi = Z - np.nanmin(Z)
    return mu_grid, kap_grid, dchi


def ellipse_from_cov(mu_vec, Sigma, levels=(2.30, 4.61, 6.18, 11.83)):
    from numpy.linalg import eigh
    vals, vecs = eigh(Sigma)
    order = np.argsort(vals)
    vals = vals[order]; vecs = vecs[:, order]
    th = np.linspace(0, 2*np.pi, 360)
    out = []
    for lv in levels:
        axes = np.sqrt(np.maximum(vals, 1e-30) * lv)
        R = vecs @ np.diag(axes)
        pts = (R @ np.vstack([np.cos(th), np.sin(th)])).T + mu_vec[None, :]
        out.append((pts[:,0], pts[:,1], lv))
    return out


def kappa_C_ellipse(name: str):
    # Reuse logic from fit_kappa_C.run_one by recomputing locally (no import coupling)
    from scripts.compare_fit_multi import compute_inv1_unit
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    R = rc.R
    g_gas = (1.33*(rc.Vgas*rc.Vgas))/np.maximum(R,1e-6)
    g_star0 = (rc.Vdisk*rc.Vdisk + rc.Vbul*rc.Vbul)/np.maximum(R,1e-6)
    g_obs, eg = with_error_floor(R, rc.Vobs, rc.eV)
    img, pix = load_ha_or_proxy(name)
    k_grid = np.linspace(0.02, 1.0, 20)
    phi_k = np.exp(-(k_grid/0.6)**2)
    g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k,
                                      eta_params=EtaParams(beta=0.3, s_kpc=0.5))
    g_c  = compute_inv1_unit('disk_analytic', R, rc.SBdisk, pix_kpc=0.2, size=256, line_eps_kpc=0.8, pad_factor=2)
    m = np.isfinite(g_obs)&np.isfinite(eg)&np.isfinite(g_gas)&np.isfinite(g_star0)&np.isfinite(g_if)&np.isfinite(g_c)
    y = g_obs[m] - g_gas[m]
    X = np.stack([g_star0[m], g_if[m], g_c[m]], axis=1)
    w = 1.0/np.maximum(eg[m], 1e-6)
    WX = X * w[:, None]; Wy = y * w
    XT_WX = WX.T @ WX; XT_Wy = WX.T @ Wy
    a = np.linalg.lstsq(XT_WX, XT_Wy, rcond=None)[0]
    mu, kappa, C = [float(max(ai,0.0)) for ai in a]
    gmod = g_gas + mu*g_star0 + kappa*g_if + C*g_c
    c2 = chi2(g_obs[m], eg[m], gmod[m]); N = int(np.sum(m)); k = 3
    sigma2 = float(c2 / max(N-k, 1))
    try:
        cov = sigma2 * np.linalg.inv(XT_WX)
    except np.linalg.LinAlgError:
        cov = sigma2 * np.linalg.pinv(XT_WX)
    # Extract 2x2 for (kappa,C)
    mu_vec = np.array([kappa, C], float)
    Sigma = np.array([[cov[1,1], cov[1,2]], [cov[2,1], cov[2,2]]], float)
    return mu_vec, Sigma, (mu, kappa, C, c2, N)


def make_page(name: str) -> str:
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    # Panel 1: (μ, κ) profile with 90% level included
    mu_g, kap_g, dchi = mu_kappa_profile(name)
    fig1, ax1 = plt.subplots(1,1, figsize=(5.4,4.2))
    cs = ax1.contour(kap_g, mu_g, dchi, levels=[2.30, 4.61, 6.18, 11.83], colors=('C0','C3','C1','C2'))
    fmt = {2.30:'68%', 4.61:'90%', 6.18:'95%', 11.83:'99.7%'}
    ax1.clabel(cs, fmt=lambda v: fmt.get(v, f"Δχ²={v:.2f}"), fontsize=8)
    ax1.set_xlabel('κ'); ax1.set_ylabel('Υ★'); ax1.set_title(f'{name}: (Υ★, κ) プロフィール尤度')
    p1 = outdir / f'{name.lower()}_mu_kappa_profile_90.png'
    fig1.tight_layout(); fig1.savefig(p1, dpi=140); plt.close(fig1)
    # Panel 2: (κ, C) ellipse with 90% level
    mu_vec, Sigma, stats_tuple = kappa_C_ellipse(name)
    ell = ellipse_from_cov(mu_vec, Sigma)
    fig2, ax2 = plt.subplots(1,1, figsize=(5.4,4.2))
    for xs, ys, lv in ell:
        ax2.plot(xs, ys, label=f'Δχ²={lv:.2f}')
    ax2.plot([mu_vec[0]],[mu_vec[1]],'ko',ms=4)
    ax2.set_xlabel('κ'); ax2.set_ylabel('C'); ax2.set_title(f'{name}: (κ, C) 等高線（68/90/95/99.7%）')
    ax2.legend(frameon=False, fontsize=8)
    p2 = outdir / f'{name.lower()}_kappaC_ellipse_90.png'
    fig2.tight_layout(); fig2.savefig(p2, dpi=140); plt.close(fig2)
    # Optional: solar-bound overlay if exists
    p_solar = outdir / f'{name.lower()}_kappaC_with_solar_bound.png'
    solar_block = ''
    if p_solar.exists():
        solar_block = f'<div class=card><p><b>Solar 上限（半平面）</b></p><p><img src="{p_solar.name}" style="max-width:100%"></p></div>'
    mu, kappa, C, c2, N = stats_tuple
    # 90%CL table (approx):
    # (1) from (μ,κ) profile grid: take Δχ²≤4.61 region and project to axes
    mask90 = (dchi <= 4.61)
    if np.any(mask90):
        mu_idx = np.where(mask90.any(axis=1))[0]
        kap_idx = np.where(mask90.any(axis=0))[0]
        mu_lo = float(mu_g[mu_idx.min()]) if mu_idx.size else float('nan')
        mu_hi = float(mu_g[mu_idx.max()]) if mu_idx.size else float('nan')
        kap_lo = float(kap_g[kap_idx.min()]) if kap_idx.size else float('nan')
        kap_hi = float(kap_g[kap_idx.max()]) if kap_idx.size else float('nan')
    else:
        mu_lo = mu_hi = kap_lo = kap_hi = float('nan')
    # (2) from (κ,C) covariance: Δχ²=4.61 ellipse projection
    from numpy.linalg import eig
    # Sample points on 90% ellipse to estimate axis ranges
    th = np.linspace(0, 2*np.pi, 360)
    from numpy.linalg import eigh
    vals, vecs = eigh(Sigma)
    axes = np.sqrt(np.maximum(vals, 1e-30) * 4.61)
    Rm = vecs @ np.diag(axes)
    pts = (Rm @ np.vstack([np.cos(th), np.sin(th)])).T + np.array([kappa, C])[None,:]
    kap_lo2, kap_hi2 = float(np.nanmin(pts[:,0])), float(np.nanmax(pts[:,0]))
    C_lo, C_hi = float(np.nanmin(pts[:,1])), float(np.nanmax(pts[:,1]))
    # Solar-bound expression if available
    solar_expr = 'K_if·κ + K_c·C ≤ a_max'
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{name}: Υ★–κ–C 90%CL</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        f'<main class="wrap"><h1>{name}: Υ★–κ–C の 90%CL 可視化</h1>',
        f'<div class=card><p>最適: Υ★={mu:.3f}, κ={kappa:.3g}, C={C:.3g}; χ²={c2:.1f} (N={N})</p>'
        '<p><small>等高線は2変数のΔχ²={2.30, 4.61, 6.18, 11.83}（68/90/95/99.7% CL）。(Υ★,κ)はプロフィール尤度、(κ,C)は線形誤差伝播からの近似楕円。</small></p></div>',
        f'<div class=card><img src="{p1.name}" style="max-width:100%"></div>',
        f'<div class=card><img src="{p2.name}" style="max-width:100%"></div>',
        '<div class=card><h3>90%CL 数表（近似）</h3>'
        f'<p>Υ★ ∈ [{mu_lo:.3f}, {mu_hi:.3f}]（(Υ★,κ) Δχ²≤4.61投影）</p>'
        f'<p>κ ∈ [{kap_lo:.3g}, {kap_hi:.3g}]（(Υ★,κ)） ∩ [{kap_lo2:.3g}, {kap_hi2:.3g}]（(κ,C)）</p>'
        f'<p>C ∈ [{C_lo:.3g}, {C_hi:.3g}]（(κ,C) Δχ²≤4.61投影）</p>'
        f'<p><small>Solar上限の式（規格化）: {solar_expr}</small></p></div>',
        solar_block,
        '</main></body></html>'
    ]
    out = outdir / f'{name.lower()}_ykc_90.html'
    out.write_text('\n'.join(html), encoding='utf-8')
    return str(out)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='Build combined Υ★–κ–C 90%CL visualization pages')
    ap.add_argument('--names', type=str, default='NGC3198,NGC2403')
    args = ap.parse_args()
    names = [n.strip() for n in args.names.split(',') if n.strip()]
    outs = [make_page(nm) for nm in names]
    for p in outs:
        print('wrote', p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
