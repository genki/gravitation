#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Tuple

from scripts.utils.mpl_fonts import use_jp_font
from scripts.fit_sparc_fdbl import read_sparc_massmodels, make_axisymmetric_image
from scripts.compare_fit_multi import chi2, to_accel
from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_profile_from_map


def with_error_floor(R, Vobs, eV):
    Vobs = np.asarray(Vobs, float); eV = np.asarray(eV, float)
    floor = np.clip(0.03*np.abs(Vobs), 3.0, 7.0)
    eVe = np.sqrt(np.maximum(eV,1e-6)**2 + floor**2)
    return to_accel(R, Vobs, eVe)


def load_ha_or_proxy(name: str) -> Tuple[np.ndarray, float]:
    from astropy.io import fits
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


def downsample_avg(img: np.ndarray, factor: int) -> np.ndarray:
    if factor <= 1:
        return img
    h, w = img.shape[:2]
    nh = (h // factor) * factor
    nw = (w // factor) * factor
    if nh < factor or nw < factor:
        return img
    cropped = img[:nh, :nw]
    sh = cropped.reshape(nh // factor, factor, nw // factor, factor)
    return np.nanmean(np.nanmean(sh, axis=3), axis=1)


def fit_mu_given_kappa(g_obs, eg, g_gas, g_star0, g_if, mask, kappa: float) -> float:
    m = mask & np.isfinite(g_if)
    if not np.any(m):
        return 0.7
    w = 1.0 / np.maximum(eg[m], 1e-6)
    X1 = g_star0[m]
    Y = g_obs[m] - g_gas[m] - kappa*g_if[m]
    denom = float(np.nansum(w * X1 * X1))
    if denom <= 0:
        return 0.7
    mu = float(np.nansum(w * X1 * Y)) / denom
    return mu


def main() -> int:
    use_jp_font()
    import argparse
    ap = argparse.ArgumentParser(description='Phi·eta profile likelihood and correlations')
    ap.add_argument('--name', required=True)
    ap.add_argument('--beta', type=float, required=True)
    ap.add_argument('--s', type=float, required=True)
    ap.add_argument('--sgk', type=float, required=True)
    ap.add_argument('--max-size', type=int, default=256)
    ap.add_argument('--quick', action='store_true')
    args = ap.parse_args()

    nm = args.name
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), nm)
    R = rc.R
    g_gas = (1.33*(rc.Vgas*rc.Vgas))/np.maximum(R,1e-6)
    g_star0 = (rc.Vdisk*rc.Vdisk+rc.Vbul*rc.Vbul)/np.maximum(R,1e-6)
    g_obs, eg = with_error_floor(R, rc.Vobs, rc.eV)

    # W·S baseline
    from scripts.compare_fit_multi import line_bias_accel
    g_ws = line_bias_accel(R, rc.SBdisk, pix_kpc=0.2, size=256, line_eps_kpc=0.8, pad_factor=2)
    m_ws = np.isfinite(g_obs)&np.isfinite(eg)&np.isfinite(g_gas)&np.isfinite(g_star0)&np.isfinite(g_ws)
    # Phi·eta term
    img, pix = load_ha_or_proxy(nm)
    H, W = img.shape[:2]
    max_dim = max(H, W)
    if max_dim > args.max_size:
        fac = int(np.ceil(max_dim / float(args.max_size)))
        img = downsample_avg(img, fac)
        pix = pix * fac
    k_grid = np.linspace(0.02, 1.2, 16 if args.quick else 24)
    phi_k = np.exp(-(k_grid/args.sgk)**2)
    g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k, eta_params=EtaParams(beta=args.beta, s_kpc=args.s))
    m = m_ws & np.isfinite(g_if)
    # best-fit (k=2) for reference
    # closed-form 2-parameter fit
    w = 1.0 / np.maximum(eg[m], 1e-6)
    X1 = g_star0[m]; X2 = g_if[m]
    Y  = g_obs[m] - g_gas[m]
    S11 = float(np.nansum(w*X1*X1)); S22 = float(np.nansum(w*X2*X2)); S12 = float(np.nansum(w*X1*X2))
    b1  = float(np.nansum(w*X1*Y));   b2  = float(np.nansum(w*X2*Y))
    det = S11*S22 - S12*S12
    mu_b, kap_b = (0.7, 0.0)
    if det > 0:
        mu_b = (b1*S22 - b2*S12) / det
        kap_b = (S11*b2 - S12*b1) / det

    def aicc(chi, k, N):
        return float(chi + 2*k + (2*k*(k+1))/max(N-k-1,1))

    chi_min = chi2(g_obs[m], eg[m], (g_gas+mu_b*g_star0+kap_b*g_if)[m])
    aicc_min = aicc(chi_min, 2, int(np.sum(m)))

    # profile vs kappa (optimize mu at each kappa)
    k0 = max(abs(kap_b), 1e-4)
    k_lo = k0/100.0
    k_hi = k0*100.0
    kap_grid = np.logspace(np.log10(k_lo), np.log10(k_hi), 160)
    prof_chi = []
    prof_aicc = []
    prof_mu = []
    for kap in kap_grid:
        mu = fit_mu_given_kappa(g_obs, eg, g_gas, g_star0, g_if, m, kap)
        prof_mu.append(mu)
        ch = chi2(g_obs[m], eg[m], (g_gas+mu*g_star0+kap*g_if)[m])
        prof_chi.append(ch)
        prof_aicc.append(aicc(ch, 2, int(np.sum(m))))
    prof_chi = np.asarray(prof_chi); prof_aicc = np.asarray(prof_aicc); prof_mu = np.asarray(prof_mu)

    # determine 95% CL using Δχ²=3.84 (1 dof)
    dchi = prof_chi - float(chi_min)
    try:
        import numpy as _np
        ok = dchi >= 0
        # find crossing points around minimum
        i_min = int(np.argmin(dchi))
        left = _np.where(dchi[:i_min] >= 3.84)[0]
        right = _np.where(dchi[i_min:] >= 3.84)[0]
        k_lo95 = kap_grid[left[-1]] if left.size else kap_grid[0]
        k_hi95 = kap_grid[i_min+right[0]] if right.size else kap_grid[-1]
    except Exception:
        k_lo95, k_hi95 = kap_grid[0], kap_grid[-1]

    # plots
    outdir = Path('server/public/reports')
    outdir.mkdir(parents=True, exist_ok=True)

    # profile plot
    fig, ax = plt.subplots(1,1, figsize=(6.2,4.4))
    ax.plot(kap_grid, dchi, color='C3', lw=1.5, label='Δχ²(kappa)')
    ax.axhline(3.84, color='0.5', ls='--', lw=1.0, label='95% CL (Δχ²=3.84)')
    ax.axvline(kap_b, color='C0', ls='-', lw=1.2, label=f'best κ={kap_b:.3g}')
    ax.fill_between(kap_grid, 0, 3.84, where=(kap_grid>=k_lo95)&(kap_grid<=k_hi95), color='C3', alpha=0.15, label='95%区間')
    ax.set_xscale('log'); ax.set_xlabel('κ (info-flow scale)'); ax.set_ylabel('Δχ²')
    ax.set_title(f'{nm} — Φ×η κ プロファイル（β={args.beta}, s={args.s} kpc, σ_k={args.sgk})')
    ax.legend(loc='best', fontsize=9)
    prof_png = outdir / f'{nm.lower()}_phieta_profile.png'
    fig.tight_layout(); fig.savefig(prof_png, dpi=140); plt.close(fig)

    # mu vs kappa along profile
    fig, ax = plt.subplots(1,1, figsize=(6.0,4.0))
    ax.plot(kap_grid, prof_mu, color='C2', lw=1.4)
    ax.set_xscale('log'); ax.set_xlabel('κ'); ax.set_ylabel('μ (Υ★scale)')
    ax.set_title(f'{nm} — μ(κ) プロファイル関係')
    mu_png = outdir / f'{nm.lower()}_mu_vs_kappa.png'
    fig.tight_layout(); fig.savefig(mu_png, dpi=140); plt.close(fig)

    # correlations from trials
    trials = Path('data/results/ws_vs_phieta_trials.ndjson')
    k_ss, s_ss, sg_ss, d_ss, b_ss = [], [], [], [], []
    if trials.exists():
        for ln in trials.read_text(encoding='utf-8').splitlines():
            try:
                row = json.loads(ln)
            except Exception:
                continue
            if row.get('name') != nm:
                continue
            if not row.get('ok'):
                continue
            k_ss.append(float(row.get('kappa', np.nan)))
            s_ss.append(float(row.get('s_kpc', np.nan)))
            sg_ss.append(float(row.get('sgk', np.nan)))
            d_ss.append(float(row.get('delta', np.nan)))
            b_ss.append(float(row.get('beta', np.nan)))
    k_ss = np.asarray(k_ss); s_ss=np.asarray(s_ss); sg_ss=np.asarray(sg_ss); d_ss=np.asarray(d_ss); b_ss=np.asarray(b_ss)

    def _scatter(x, y, c, xlabel, ylabel, title, fname):
        fig, ax = plt.subplots(1,1, figsize=(5.6,4.2))
        sc = ax.scatter(x, y, c=c, cmap='coolwarm', s=18, alpha=0.9, edgecolors='none')
        cb = fig.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        cb.set_label('ΔAICc (Φ×η − W·S)')
        ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
        ax.set_title(title)
        out = outdir / fname
        fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
        return out

    scat1 = scat2 = None
    if k_ss.size:
        scat1 = _scatter(s_ss, k_ss, d_ss, 's [kpc]', 'κ', f'{nm} — κ vs s（着色=ΔAICc）', f'{nm.lower()}_kappa_vs_s.png')
        scat2 = _scatter(sg_ss, k_ss, d_ss, 'σ_k', 'κ', f'{nm} — κ vs σ_k（着色=ΔAICc）', f'{nm.lower()}_kappa_vs_sigk.png')

    # HTML report
    parts = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{nm} Φ×η プロファイル/相関</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        f'<main class="wrap"><h1>{nm} — Φ×η プロファイル尤度と相関</h1>',
        f'<p>条件: β={args.beta}, s={args.s} kpc, σ_k={args.sgk}, 画像max={args.max_size}, k格子={len(k_grid)}点。</p>',
        f'<div class=card><p>best: μ={mu_b:.3g}, κ={kap_b:.3g}, χ²_min={chi_min:.2f}, AICc_min={aicc_min:.2f}<br>',
        f'95% CL (Δχ²=3.84) → κ ∈ [{k_lo95:.3g}, {k_hi95:.3g}]</p></div>',
        f'<img src="{prof_png.name}" alt="profile">',
        f'<img src="{mu_png.name}" alt="mu_vs_kappa">'
    ]
    if scat1:
        parts.append(f'<img src="{scat1.name}" alt="kappa_vs_s">')
    if scat2:
        parts.append(f'<img src="{scat2.name}" alt="kappa_vs_sigk">')
    parts.append('</main></body></html>')
    html = outdir / f'{nm.lower()}_phieta_profile.html'
    html.write_text('\n'.join(parts), encoding='utf-8')
    print('wrote', html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

