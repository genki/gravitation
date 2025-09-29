#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

from scripts.fit_sparc_fdbl import read_sparc_massmodels, make_axisymmetric_image
from scripts.compare_fit_multi import chi2, to_accel, line_bias_accel
from scripts.utils.progress import ProgressETA
from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_profile_from_map
from astropy.io import fits


def load_halpha_or_proxy(name: str) -> tuple[np.ndarray, float]:
    p = Path(f'data/halpha/{name}/Halpha_SB.fits')
    if p.exists():
        img = fits.getdata(p).astype(float)
        hdr = fits.getheader(p)
        pix = float(hdr.get('PIXSCALE', 0.305)) / 206265.0 * 1.0  # rough kpc/pix fallback
        # If WCS is not reliable, fall back to 0.2 kpc/pix
        if not np.isfinite(pix) or pix <= 0:
            pix = 0.2
        # downsample very large maps to keep memory/time bounded
        maxdim = max(img.shape)
        if maxdim > 1200:
            import scipy.ndimage as ndi
            scale = 800.0 / maxdim
            img = ndi.zoom(img, zoom=scale, order=1)
            pix = pix / scale
        return img, pix
    # fallback: build proxy from 3.6um SB (rotationally symmetric)
    rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), name)
    R = rc.R
    SB = rc.SBdisk
    img = make_axisymmetric_image(R, SB, pix_kpc=0.2, size=256)
    return img, 0.2


def aicc(AIC: float, k: int, N: int) -> float:
    return float(AIC + (2*k*(k+1)) / max(N-k-1, 1))


def with_error_floor(R: np.ndarray, Vobs: np.ndarray, eV: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Apply site‑wide velocity error floor and return (g_obs, eg) in accel space.

    Floor policy: dV_floor = clip(0.03*|Vobs|, 3..7) km/s; eV_eff = sqrt(eV^2 + dV_floor^2);
    eg = 2 V eV_eff / R.
    """
    Vobs = np.asarray(Vobs, float); eV = np.asarray(eV, float)
    floor = np.clip(0.03 * np.abs(Vobs), 3.0, 7.0)
    eVe = np.sqrt(np.maximum(eV, 1e-6) ** 2 + floor ** 2)
    g_obs, eg = to_accel(R, Vobs, eVe)
    return g_obs, eg


def compare_one(name: str,
                beta_list: list[float],
                kgrid_lo: float,
                kgrid_hi: float,
                kgrid_n: int,
                pix_kpc: float,
                size: int) -> dict:
    rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), name)
    R = rc.R
    Vobs = rc.Vobs
    eV = np.maximum(rc.eV, 1e-6)
    g_gas = (1.33 * (rc.Vgas*rc.Vgas)) / np.maximum(R, 1e-6)
    g_star0 = (rc.Vdisk*rc.Vdisk + rc.Vbul*rc.Vbul) / np.maximum(R, 1e-6)
    g_obs, eg = with_error_floor(R, Vobs, eV)
    # Surface (W·S ≈ log-irradiance kernel)
    g_ws = line_bias_accel(R, rc.SBdisk, pix_kpc=pix_kpc, size=size, line_eps_kpc=0.8, pad_factor=2)
    # Build common mask
    m_base = np.isfinite(g_obs) & np.isfinite(eg) & np.isfinite(g_gas) & np.isfinite(g_star0) & np.isfinite(g_ws)
    # Weighted LS for [mu, alpha] with design [g_star0, g_extra]
    def fit_mu_alpha(g_extra: np.ndarray, mask: np.ndarray) -> tuple[float,float]:
        mb = mask & np.isfinite(g_extra)
        w = 1.0 / np.maximum(eg[mb], 1e-6)
        X1 = g_star0[mb]; X2 = g_extra[mb]
        Y = g_obs[mb] - g_gas[mb]
        # normal equations for weighted LS
        W = w
        S11 = float(np.nansum(W*X1*X1)); S22 = float(np.nansum(W*X2*X2)); S12 = float(np.nansum(W*X1*X2))
        b1 = float(np.nansum(W*X1*Y)); b2 = float(np.nansum(W*X2*Y))
        det = S11*S22 - S12*S12
        if det <= 0:
            return 0.7, 0.0
        mu = (b1*S22 - b2*S12) / det
        alpha = (S11*b2 - S12*b1) / det
        return float(mu), float(alpha)
    mu_ws, a_ws = fit_mu_alpha(g_ws, m_base)
    gmod_ws = g_gas + mu_ws * g_star0 + a_ws * g_ws
    chi_ws = chi2(g_obs[m_base], eg[m_base], gmod_ws[m_base])
    # Info model (Phi·eta)
    img, pix = load_halpha_or_proxy(name)
    k_grid = np.linspace(kgrid_lo, kgrid_hi, int(max(kgrid_n, 4)))
    phi_k = np.exp(-(k_grid/0.6)**2)  # band-limit (shared across galaxies)
    best_if = None
    for beta in beta_list:
        eta_p = EtaParams(beta=float(beta), s_kpc=0.5)
        g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k, eta_params=eta_p)
        m_all = m_base & np.isfinite(g_if)
        if not np.any(m_all):
            continue
        mu_if, a_if = fit_mu_alpha(g_if, m_all)
        gmod_if = g_gas + mu_if * g_star0 + a_if * g_if
        chi_if = chi2(g_obs[m_all], eg[m_all], gmod_if[m_all])
        val = (chi_if, mu_if, a_if, beta, int(np.sum(m_all)))
        if best_if is None or val[0] < best_if[0]:
            best_if = val
    if best_if is None:
        raise RuntimeError('Phi·eta failed for all beta settings')
    chi_if, mu_if, a_if, beta_best, N_if = best_if
    # Identical N across models = intersection mask
    m = m_all
    N = int(np.sum(m))
    out = {
        'name': name,
        'N': N,
        'k': 2,
        'chi2_ws': float(chi_ws),
        'chi2_if': float(chi_if),
        'AICc_ws': float(aicc(chi_ws + 2*2, 2, N)),
        'AICc_if': float(aicc(chi_if + 2*2, 2, N)),
        'mu_ws': mu_ws,
        'alpha_ws': a_ws,
        'mu_if': mu_if,
        'kappa_if': a_if,
        'beta_if': float(beta_best),
    }
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='Compare W·S vs Phi·eta on a list of galaxies (fair protocol)')
    ap.add_argument('--names', type=str, default='', help='comma-separated galaxy names (override rep6.txt)')
    ap.add_argument('--beta-list', type=str, default='0.0,0.3,0.6', help='comma-separated beta values for Phi·eta forwardization')
    ap.add_argument('--k-grid', type=str, default='0.02,1.0,16', help='kmin,kmax,N for spectral grid')
    ap.add_argument('--pix-kpc', type=float, default=0.2, help='common pixel scale [kpc/pix] for surface kernels')
    ap.add_argument('--size', type=int, default=256, help='common grid size for surface kernels')
    args = ap.parse_args()
    if args.names:
        names = [nm.strip() for nm in args.names.split(',') if nm.strip()]
    else:
        names = [ln.strip() for ln in Path('data/sparc/sets/rep6.txt').read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.startswith('#')]
    pg = ProgressETA([(f'gal:{nm}', 1.0) for nm in names] + [('html', 1.0)])
    pg.start(total_hint_min=max(len(names) * 0.2, 1.0))
    rows = []
    kmin,kmax,kn = [float(x) for x in args.k_grid.split(',')]
    beta_list = [float(b) for b in args.beta_list.split(',') if b!='']
    for nm in names:
        try:
            rows.append(compare_one(nm, beta_list=beta_list, kgrid_lo=kmin, kgrid_hi=kmax, kgrid_n=int(kn), pix_kpc=args.pix_kpc, size=int(args.size)))
        except Exception as e:
            rows.append({'name': nm, 'error': str(e)})
        finally:
            pg.tick(f'gal:{nm}')
    # Merge with existing partial results (cumulative across chunks)
    store = Path('data/results/ws_vs_phieta_rows.json')
    try:
        if store.exists():
            old = json.loads(store.read_text(encoding='utf-8'))
        else:
            old = []
    except Exception:
        old = []
    # build dict by name to de-duplicate
    by_name = {r.get('name'): r for r in old if isinstance(r, dict) and 'name' in r}
    for r in rows:
        nm = r.get('name') if isinstance(r, dict) else None
        if nm:
            by_name[nm] = r
    merged = [by_name[k] for k in sorted(by_name.keys())]
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_text(json.dumps(merged, indent=2), encoding='utf-8')

    # HTML
    out_dir = Path('server/public/reports'); out_dir.mkdir(parents=True, exist_ok=True)
    rep = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>W·S vs Phi·eta (rep6)</title><link rel="stylesheet" href="../styles.css"></head><body>',
           '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
           '<main class="wrap"><h1>W·S（界面） vs Phi·eta（情報流）— 代表6銀河</h1>']
    rep.append('<table><thead><tr><th>Galaxy</th><th>AICc (W·S)</th><th>AICc (Phi·eta)</th><th>ΔAICc (Phi·eta − W·S)</th><th>N</th><th>k</th><th>β*</th></tr></thead><tbody>')
    wins = 0
    deltas = []
    for r in merged:
        if 'error' in r:
            rep.append(f"<tr><td>{r['name']}</td><td colspan=5><small>error: {r['error']}</small></td></tr>")
            continue
        d = float(r['AICc_if'] - r['AICc_ws'])
        deltas.append(d)
        if d < 0: wins += 1
        rep.append(f"<tr><td>{r['name']}</td><td>{r['AICc_ws']:.2f}</td><td>{r['AICc_if']:.2f}</td><td>{d:.2f}</td><td>{r['N']}</td><td>2</td><td>{r.get('beta_if', float('nan')):.2f}</td></tr>")
    rep.append('</tbody></table>')
    # Summary stats: median[IQR] and Cohen's d across galaxies
    if deltas:
        arr = np.asarray(deltas, float)
        med = float(np.nanmedian(arr))
        q1, q3 = float(np.nanpercentile(arr, 25)), float(np.nanpercentile(arr, 75))
        iqr = q3 - q1
        mean = float(np.nanmean(arr)); std = float(np.nanstd(arr, ddof=1) if len(arr) > 1 else 0.0)
        d_eff = (mean / std) if std > 0 else float('nan')
        rep.append('<div class=card>'
                   f'<p>勝率(Phi·eta): {wins} / {len(deltas)} （ΔAICc<0 を勝ちと定義）</p>'
                   f'<p>ΔAICc(Phi·eta−W·S) 中央値[IQR]: {med:.2f} [{iqr:.2f}] ／ 効果量 d≈{d_eff:.2f}</p>'
                   '<p><small>誤差床: clip(0.03×Vobs, 3..7) km/s。N・k は両方式で同一（k=1: Υ★）。</small></p></div>')
    else:
        rep.append('<div class=card><p><small>有効な比較行がありませんでした。</small></p></div>')
    # Persist JSON summary alongside rows
    summary = {
        'wins_if': wins,
        'n': int(len(deltas)),
        'median_delta_aicc': med if deltas else None,
        'iqr_delta_aicc': iqr if deltas else None,
        'cohens_d': d_eff if deltas else None,
    }
    (out_dir / 'ws_vs_phieta_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    rep.append('</main></body></html>')
    (out_dir / 'ws_vs_phieta_rep6.html').write_text('\n'.join(rep), encoding='utf-8')
    print('wrote', out_dir / 'ws_vs_phieta_rep6.html')
    pg.tick('html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
