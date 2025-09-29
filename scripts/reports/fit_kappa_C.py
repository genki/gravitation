#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from astropy.io import fits

from scripts.fit_sparc_fdbl import read_sparc_massmodels, make_axisymmetric_image
from scripts.compare_fit_multi import to_accel, chi2, compute_inv1_unit
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
        # downsample very large to stabilize
        if max(img.shape) > 1200:
            import scipy.ndimage as ndi
            img = ndi.zoom(img, zoom=800.0/max(img.shape), order=1)
        return img, pix
    # fallback: axisymmetric proxy from SBdisk
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    return make_axisymmetric_image(rc.R, rc.SBdisk, pix_kpc=0.2, size=256), 0.2


def fit_linear_params(y, X, w):
    # Weighted LS: minimize ||W (X a - y)||^2, W=diag(w)
    WX = X * w[:, None]
    Wy = y * w
    XT_WX = WX.T @ WX
    XT_Wy = WX.T @ Wy
    try:
        a = np.linalg.solve(XT_WX, XT_Wy)
    except np.linalg.LinAlgError:
        a = np.linalg.lstsq(XT_WX, XT_Wy, rcond=None)[0]
    return a, XT_WX


def ellipse_from_cov(mu, Sigma, levels=(2.30, 6.18, 11.83)):
    # returns list of (xs, ys, level)
    from numpy.linalg import eigh
    vals, vecs = eigh(Sigma)
    order = np.argsort(vals)
    vals = vals[order]; vecs = vecs[:, order]
    out = []
    th = np.linspace(0, 2*np.pi, 360)
    for lv in levels:
        axes = np.sqrt(np.maximum(vals, 1e-30) * lv)
        R = vecs @ np.diag(axes)
        pts = (R @ np.vstack([np.cos(th), np.sin(th)])).T + mu[None, :]
        out.append((pts[:,0], pts[:,1], lv))
    return out


def _prior_ratio_from_phi_k(k_grid: np.ndarray, phi_k: np.ndarray, beta: float = 0.0) -> float:
    """Compute prior ratio r ≈ C/κ from small-k eta model.

    Using eta_small_k ∝ k^2 (orientation avg absorbed), closures give
      κ ∝ ∫ phi_k(k) k^2 dk,
      C ∝ ∫ phi_k(k) k   dk.
    So r ≈ (∫ phi_k k dk)/(∫ phi_k k^2 dk). Independent of s.
    Optionally modulate by a shallow β forwardization (treated as ~O(1)).
    """
    num = float(np.trapz(phi_k * k_grid, k_grid))
    den = float(np.trapz(phi_k * (k_grid ** 2), k_grid))
    if den <= 0:
        return 0.0
    r = num / den
    # mild β dependence (kept conservative)
    r *= (1.0 + 0.1 * float(beta))
    return float(r)


def run_one(name: str,
            prior: str = 'none',
            prior_strength: float = 0.0,
            prior_beta: float = 0.3,
            prior_s_kpc: float = 0.5) -> dict:
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    R = rc.R
    g_gas = (1.33*(rc.Vgas*rc.Vgas))/np.maximum(R,1e-6)
    g_star0 = (rc.Vdisk*rc.Vdisk + rc.Vbul*rc.Vbul)/np.maximum(R,1e-6)
    g_obs, eg = with_error_floor(R, rc.Vobs, rc.eV)
    # Design columns (追加項): info-flow and 1/r (disk analytic)
    img, pix = load_ha_or_proxy(name)
    k_grid = np.linspace(0.02, 1.0, 20)
    phi_k = np.exp(-(k_grid/0.6)**2)
    g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k,
                                      eta_params=EtaParams(beta=0.3, s_kpc=0.5))
    g_c  = compute_inv1_unit('disk_analytic', R, rc.SBdisk, pix_kpc=0.2, size=256, line_eps_kpc=0.8, pad_factor=2)
    # Common finite mask
    m = np.isfinite(g_obs)&np.isfinite(eg)&np.isfinite(g_gas)&np.isfinite(g_star0)&np.isfinite(g_if)&np.isfinite(g_c)
    if np.sum(m) < 10:
        return {'name': name, 'ok': False, 'reason': 'insufficient points'}
    y = g_obs[m] - g_gas[m]
    X = np.stack([g_star0[m], g_if[m], g_c[m]], axis=1)
    w = 1.0/np.maximum(eg[m], 1e-6)
    # Unconstrained (ML)
    a, XT_WX = fit_linear_params(y, X, w)
    mu, kappa, C = [float(max(ai, 0.0)) for ai in a]
    gmod = g_gas + mu*g_star0 + kappa*g_if + C*g_c
    c2 = chi2(g_obs[m], eg[m], gmod[m])
    N = int(np.sum(m)); k = 3
    A = float(c2 + 2*k + (2*k*(k+1))/max(N-k-1,1))
    # Covariance (approx.): sigma2 * (X^T W X)^-1, sigma2 ~ chi2/(N-k)
    sigma2 = float(c2 / max(N-k, 1))
    try:
        cov = sigma2 * np.linalg.inv(XT_WX)
    except np.linalg.LinAlgError:
        cov = sigma2 * np.linalg.pinv(XT_WX)
    # Optional prior: enforce (C − r κ) ≈ 0 with ridge λ
    map_obj = None
    map_cov = None
    r_ratio = None
    if prior and prior != 'none' and prior_strength > 0:
        r_ratio = _prior_ratio_from_phi_k(k_grid, phi_k,
                                          beta=(prior_beta if prior == 'phase' else 0.0))
        # Penalty on (C - r κ)^2 with weight λ ≡ prior_strength
        lam = float(prior_strength)
        P = np.zeros((3, 3), dtype=float)
        # add to κκ, κC, Cκ, CC
        P[1, 1] += lam * (r_ratio ** 2)
        P[1, 2] += -lam * r_ratio
        P[2, 1] += -lam * r_ratio
        P[2, 2] += lam
        # Solve (X^T W X + P) a = X^T W y  (zero-mean on penalty)
        XT_WX_map = XT_WX + P
        try:
            a_map = np.linalg.solve(XT_WX_map, X.T @ (w * y))
        except np.linalg.LinAlgError:
            a_map = np.linalg.lstsq(XT_WX_map, X.T @ (w * y), rcond=None)[0]
        mu_m, kap_m, C_m = [float(max(ai, 0.0)) for ai in a_map]
        gmod_m = g_gas + mu_m*g_star0 + kap_m*g_if + C_m*g_c
        c2_m = chi2(g_obs[m], eg[m], gmod_m[m])
        A_m = float(c2_m + 2*3 + (2*3*(3+1))/max(N-3-1,1))
        sigma2_m = float(c2_m / max(N-3, 1))
        try:
            map_cov = sigma2_m * np.linalg.inv(XT_WX_map)
        except np.linalg.LinAlgError:
            map_cov = sigma2_m * np.linalg.pinv(XT_WX_map)
        map_obj = {
            'mu': mu_m, 'kappa': kap_m, 'C': C_m,
            'chi2': c2_m, 'AICc': A_m,
        }

    # Ellipse for (kappa, C)
    mu_vec = np.array([kappa, C])
    Sigma_sub = np.array([[cov[1,1], cov[1,2]], [cov[2,1], cov[2,2]]], dtype=float)
    xs = []
    ell = ellipse_from_cov(mu_vec, Sigma_sub)
    # Plot ellipse
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1,1, figsize=(5.6,4.4))
    for Xs, Ys, lv in ell:
        ax.plot(Xs, Ys, label=f'Δχ²={lv:.2f}')
    ax.plot([kappa], [C], 'o', color='k', ms=4)
    if map_obj is not None and map_cov is not None:
        # overlay MAP ellipse
        mu_map = np.array([map_obj['kappa'], map_obj['C']], dtype=float)
        Sigma_map = np.array([[map_cov[1,1], map_cov[1,2]], [map_cov[2,1], map_cov[2,2]]], dtype=float)
        ell_map = ellipse_from_cov(mu_map, Sigma_map)
        for Xs, Ys, lv in ell_map:
            ax.plot(Xs, Ys, color='tab:orange', linestyle='--', label=f'MAP Δχ²={lv:.2f}')
        ax.plot([mu_map[0]], [mu_map[1]], 'o', color='tab:orange', ms=4)
    ax.set_xlabel('κ'); ax.set_ylabel('C'); ax.set_title(f'{name}: (κ,C) 90%CL 等高線')
    ax.legend(frameon=False, fontsize=8)
    # caption note in HTML: explain σ² and CL levels
    p_png = outdir / f'{name.lower()}_kappaC_ellipse.png'
    fig.tight_layout(); fig.savefig(p_png, dpi=140); plt.close(fig)
    # HTML
    htm = outdir / f'{name.lower()}_kappaC_fit.html'
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{name}: κ,C のフィット</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        f'<main class="wrap"><h1>{name}: Υ★, κ, C の線形適合</h1>',
        f'<div class=card><p>最適: μ={mu:.3f}, κ={kappa:.3g}, C={C:.3g}</p>',
        f'<p>χ²={c2:.2f}, AICc={A:.2f} (N={N}, k=3)</p>',
        '<p><small>設計行列: X=[g★, g_if, g_1/r]。重み w=1/eg。cov≈σ²(XᵀWX)⁻¹, σ²=χ²/(N−k)。'
        ' 等高線: Δχ²={2.30, 6.18, 11.83}（それぞれ約 68%, 95%, 99.7% CL 相当, 2変数）。</small></p></div>',
        f'<div class=card><img src="{p_png.name}" style="max-width:100%"></div>',
    ]
    if map_obj is not None:
        html.extend([
            '<div class=card><p><b>閉包事前 (C≈r·κ) を用いたMAP推定</b></p>',
            f'<p>prior={prior}, r=C/κ≈{r_ratio:.3g}, λ={prior_strength:.3g}</p>',
            f'<p>MAP: μ={map_obj["mu"]:.3f}, κ={map_obj["kappa"]:.3g}, C={map_obj["C"]:.3g}; '
            f'χ²={map_obj["chi2"]:.2f}, AICc={map_obj["AICc"]:.2f}</p>',
            '<p><small>ペナルティ: λ(C−rκ)² を尤度に加えた二次型事前。r は φ_k と小k η から算出。</small></p></div>'
        ])
    html.extend([
            '</main></body></html>'])
    htm.write_text('\n'.join(html), encoding='utf-8')
    # JSON
    js = {'name': name, 'ok': True, 'mu': mu, 'kappa': kappa, 'C': C, 'chi2': c2, 'AICc': A, 'N': N, 'k': k,
          'cov': [[float(cov[i,j]) for j in range(3)] for i in range(3)]}
    return js


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='Fit (Υ★, κ, C) with info-flow and 1/r; optional closure prior on (κ,C)')
    ap.add_argument('--names', type=str, default='NGC3198,NGC2403')
    ap.add_argument('--prior', type=str, default='none', choices=['none', 'square', 'phase'], help='closure prior type')
    ap.add_argument('--prior-strength', type=float, default=0.0, help='ridge weight λ for (C−rκ)²')
    ap.add_argument('--beta', type=float, default=0.3, help='β for phase prior (if prior=phase)')
    ap.add_argument('--s', type=float, default=0.5, help='s[kpc] for prior computation (currently cancels in r)')
    args = ap.parse_args()
    names = [n.strip() for n in args.names.split(',') if n.strip()]
    out = []
    for nm in names:
        try:
            out.append(run_one(nm, prior=args.prior, prior_strength=args.prior_strength,
                               prior_beta=args.beta, prior_s_kpc=args.s))
        except Exception as e:
            out.append({'name': nm, 'ok': False, 'reason': str(e)})
    Path('data/results').mkdir(parents=True, exist_ok=True)
    Path('data/results/kappaC_fit.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('wrote data/results/kappaC_fit.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
