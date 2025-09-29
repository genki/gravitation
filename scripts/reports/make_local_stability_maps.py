#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.fit_sparc_fdbl import read_sparc_massmodels
from scripts.compare_fit_multi import chi2
from scripts.reports.sweep_phieta_fair import with_error_floor, load_ha_or_proxy, downsample_avg
from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_profile_from_map


def fit_mu_alpha(g_obs, eg, g_gas, g_star0, g_add, mask):
    mb = mask & np.isfinite(g_add)
    if not np.any(mb):
        return 0.7, 0.0
    w = 1.0 / np.maximum(eg[mb], 1e-6)
    X1 = g_star0[mb]; X2 = g_add[mb]
    Y  = g_obs[mb] - g_gas[mb]
    S11 = float(np.nansum(w*X1*X1)); S22 = float(np.nansum(w*X2*X2)); S12 = float(np.nansum(w*X1*X2))
    b1  = float(np.nansum(w*X1*Y));   b2  = float(np.nansum(w*X2*Y))
    det = S11*S22 - S12*S12
    if det <= 0: return 0.7, 0.0
    mu = (b1*S22 - b2*S12) / det
    a  = (S11*b2 - S12*b1) / det
    return float(mu), float(a)


def aicc(chi, k, N):
    return float(chi + 2*k + (2*k*(k+1))/max(N-k-1,1))


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='Local stability heatmaps (ΔAICc) and radial rχ² difference (IF−WS)')
    ap.add_argument('--name', required=True)
    ap.add_argument('--s0', type=float, required=True)
    ap.add_argument('--sgk0', type=float, required=True)
    ap.add_argument('--beta', type=float, default=0.3)
    ap.add_argument('--max-size', type=int, default=192)
    args = ap.parse_args()
    nm = args.name
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), nm)
    R = rc.R
    g_gas = (1.33*(rc.Vgas*rc.Vgas))/np.maximum(R,1e-6)
    g_star0 = (rc.Vdisk*rc.Vdisk+rc.Vbul*rc.Vbul)/np.maximum(R,1e-6)
    g_obs, eg = with_error_floor(R, rc.Vobs, rc.eV)
    # WS baseline
    from scripts.compare_fit_multi import line_bias_accel
    g_ws = line_bias_accel(R, rc.SBdisk, pix_kpc=0.2, size=256, line_eps_kpc=0.8, pad_factor=2)
    m_ws = np.isfinite(g_obs)&np.isfinite(eg)&np.isfinite(g_gas)&np.isfinite(g_star0)&np.isfinite(g_ws)
    mu_ws, a_ws = fit_mu_alpha(g_obs, eg, g_gas, g_star0, g_ws, m_ws)
    model_ws = (g_gas + mu_ws*g_star0 + a_ws*g_ws)
    chi_ws = chi2(g_obs[m_ws], eg[m_ws], model_ws[m_ws])
    N_ws = int(np.sum(m_ws)); A_ws = aicc(chi_ws, 2, N_ws)
    # IF grid
    img, pix = load_ha_or_proxy(nm)
    # downsample
    H = getattr(img, 'shape', (0,0))[0] if hasattr(img, 'shape') else 0
    W = getattr(img, 'shape', (0,0))[1] if hasattr(img, 'shape') else 0
    if max(H,W) and max(H,W) > args.max_size:
        fac = int(np.ceil(max(H,W) / float(args.max_size)))
        img = downsample_avg(img, fac); pix *= fac
    k_grid = np.linspace(0.02, 1.2, 24)
    s_vals = np.array([args.s0 * f for f in [0.7, 0.85, 1.0, 1.15, 1.3]])
    sg_vals = np.array([args.sgk0 * f for f in [0.7, 0.85, 1.0, 1.15, 1.3]])
    heat = np.zeros((len(s_vals), len(sg_vals))) + np.nan
    for i,s in enumerate(s_vals):
        for j,sg in enumerate(sg_vals):
            phi_k = np.exp(-(k_grid/sg)**2)
            g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k,
                eta_params=EtaParams(beta=args.beta, s_kpc=float(s)))
            m = m_ws & np.isfinite(g_if)
            if not np.any(m):
                continue
            mu_if, kap = fit_mu_alpha(g_obs, eg, g_gas, g_star0, g_if, m)
            model_if = (g_gas + mu_if*g_star0 + kap*g_if)
            chi_if = chi2(g_obs[m], eg[m], model_if[m])
            A_if = aicc(chi_if, 2, int(np.sum(m)))
            heat[i,j] = float(A_if - A_ws)
    # plot heatmap
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1,1, figsize=(5.6,4.2))
    im = ax.imshow(heat, origin='lower', cmap='RdBu_r', vmin=np.nanpercentile(heat,5), vmax=np.nanpercentile(heat,95))
    ax.set_xticks(range(len(sg_vals))); ax.set_xticklabels([f'{v:.2f}' for v in sg_vals], rotation=45)
    ax.set_yticks(range(len(s_vals))); ax.set_yticklabels([f'{v:.2f}' for v in s_vals])
    ax.set_xlabel('σ_k'); ax.set_ylabel('s [kpc]'); ax.set_title(f'{nm}: ΔAICc(IF−WS) 局所ヒートマップ')
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    heat_png = outdir / f'{nm.lower()}_local_dAICc_heat.png'
    fig.tight_layout(); fig.savefig(heat_png, dpi=140); plt.close(fig)
    # radial rχ² difference (IF−WS)
    # bin radii
    edges = np.linspace(np.nanmin(R), np.nanmax(R), 12)
    rb = 0.5*(edges[:-1]+edges[1:])
    def rchi_radial(model):
        vals = []
        for a,b in zip(edges[:-1], edges[1:]):
            m = (R>=a)&(R<b)&m_ws
            if not np.any(m):
                vals.append(np.nan); continue
            c = chi2(g_obs[m], eg[m], model[m])
            vals.append(c / max(int(np.sum(m))-2, 1))
        return np.array(vals, float)
    # choose center IF
    phi_k0 = np.exp(-(k_grid/args.sgk0)**2)
    g_if0 = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k0,
        eta_params=EtaParams(beta=args.beta, s_kpc=float(args.s0)))
    m0 = m_ws & np.isfinite(g_if0)
    mu0, kap0 = fit_mu_alpha(g_obs, eg, g_gas, g_star0, g_if0, m0)
    model_if0 = (g_gas + mu0*g_star0 + kap0*g_if0)
    r_ws = rchi_radial(model_ws)
    r_if = rchi_radial(model_if0)
    fig, ax = plt.subplots(1,1, figsize=(5.8,3.8))
    ax.plot(rb, r_ws, '-o', label='WS')
    ax.plot(rb, r_if, '-o', label='IF (center)')
    ax.plot(rb, r_if - r_ws, '--', label='IF−WS')
    ax.set_xlabel('R [kpc]'); ax.set_ylabel('rχ²'); ax.legend(frameon=False)
    ax.set_title(f'{nm}: 半径別 rχ² と差分')
    rchi_png = outdir / f'{nm.lower()}_radial_rchi2.png'
    fig.tight_layout(); fig.savefig(rchi_png, dpi=140); plt.close(fig)
    # HTML
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{nm}: 局所安定性と半径別rχ²</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        f'<main class="wrap"><h1>{nm}: ΔAICc局所ヒートマップと半径別 rχ²</h1>',
        f'<div class=card><img src="{heat_png.name}" style="max-width:100%"></div>',
        f'<div class=card><img src="{rchi_png.name}" style="max-width:100%"></div>',
        '</main></body></html>'
    ]
    out_html = outdir / f'{nm.lower()}_local_stability.html'
    out_html.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out_html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

