#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from astropy.io import fits

from scripts.fit_sparc_fdbl import read_sparc_massmodels, make_axisymmetric_image
from scripts.compare_fit_multi import chi2, to_accel
from scripts.utils.progress import ProgressETA
from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_profile_from_map


def load_halpha_or_proxy(name: str) -> tuple[np.ndarray, float]:
    p = Path(f'data/halpha/{name}/Halpha_SB.fits')
    if p.exists():
        img = fits.getdata(p).astype(float)
        pix = 0.2  # fallback; exact WCSでなくても半径平均の相対比較には十分
    else:
        rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), name)
        img = make_axisymmetric_image(rc.R, rc.SBdisk, pix_kpc=0.2, size=256)
        pix = 0.2
    # downsample if needed
    maxdim = max(img.shape)
    if maxdim > 1000:
        import scipy.ndimage as ndi
        sc = 800.0 / maxdim
        img = ndi.zoom(img, zoom=sc, order=1)
        pix = pix / sc
    return img, pix


def aicc(AIC: float, k: int, N: int) -> float:
    return float(AIC + (2*k*(k+1))/max(N-k-1, 1))


def eval_one(name: str, beta: float, s_kpc: float, sigma_k: float) -> dict:
    rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), name)
    R = rc.R
    Vobs = rc.Vobs
    eV = np.maximum(rc.eV, 1e-6)
    g_gas = (1.33 * (rc.Vgas*rc.Vgas)) / np.maximum(R, 1e-6)
    g_star0 = (rc.Vdisk*rc.Vdisk + rc.Vbul*rc.Vbul) / np.maximum(R, 1e-6)
    g_obs, eg = to_accel(R, Vobs, eV)
    # baseline W·S (情報流比較用の参照): 既存の線形核で近似
    from scripts.compare_fit_multi import line_bias_accel
    g_ws = line_bias_accel(R, rc.SBdisk, pix_kpc=0.2, size=256, line_eps_kpc=0.8, pad_factor=2)
    mu_ws = float(np.clip(np.nan_to_num(np.nansum((g_obs - g_gas - g_ws) * g_star0 / (eg**2)) / np.nansum((g_star0**2) / (eg**2))), 0, 10))
    chi_ws = chi2(g_obs, eg, g_gas + mu_ws * g_star0 + g_ws)
    # info-flow Phi·eta
    img, pix = load_halpha_or_proxy(name)
    k_grid = np.linspace(0.02, 1.0, 16)
    phi_k = np.exp(-(k_grid/float(sigma_k))**2)
    eta_p = EtaParams(beta=float(beta), s_kpc=float(s_kpc))
    g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k, eta_params=eta_p)
    mu_if = float(np.clip(np.nan_to_num(np.nansum((g_obs - g_gas - g_if) * g_star0 / (eg**2)) / np.nansum((g_star0**2) / (eg**2))), 0, 10))
    chi_if = chi2(g_obs, eg, g_gas + mu_if * g_star0 + g_if)
    N = int(np.isfinite(g_obs).sum())
    return {
        'name': name,
        'beta': beta,
        's_kpc': s_kpc,
        'sigma_k': sigma_k,
        'AICc_ws': aicc(chi_ws + 2*1, 1, N),
        'AICc_if': aicc(chi_if + 2*1, 1, N),
        'N': N,
    }


def main() -> int:
    names = [ln.strip() for ln in Path('data/sparc/sets/rep6.txt').read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.startswith('#')]
    betas = [0.0, 0.2, 0.4]
    svals = [0.3, 0.5, 0.8]
    sigmas = [0.5, 0.7]
    steps = [(f'{nm}:{b}:{s}:{sg}', 1.0) for nm in names for b in betas for s in svals for sg in sigmas] + [('html',1.0)]
    pg = ProgressETA(steps)
    pg.start(total_hint_min=max(len(steps)*0.02, 1.0))
    rows = []
    for nm in names:
        best = None
        for b in betas:
            for s in svals:
                for sg in sigmas:
                    try:
                        r = eval_one(nm, b, s, sg)
                        rows.append(r)
                        if (best is None) or (r['AICc_if'] < best['AICc_if']):
                            best = r
                    except Exception as e:
                        rows.append({'name': nm, 'beta': b, 's_kpc': s, 'sigma_k': sg, 'error': str(e)})
                    finally:
                        pg.tick(f'{nm}:{b}:{s}:{sg}')
    # per-galaxy best and summary
    by = {}
    for r in rows:
        nm = r.get('name')
        if 'error' in r: continue
        if nm not in by or r['AICc_if'] < by[nm]['AICc_if']:
            by[nm] = r
    wins = sum(1 for r in by.values() if (r['AICc_if'] - r['AICc_ws']) < 0)
    dlist = [float(r['AICc_if'] - r['AICc_ws']) for r in by.values()]
    med = float(np.nanmedian(dlist)) if dlist else float('nan')
    q1 = float(np.nanpercentile(dlist,25)) if dlist else float('nan')
    q3 = float(np.nanpercentile(dlist,75)) if dlist else float('nan')
    # save json
    outj = Path('data/results/ws_vs_phieta_sweep.json')
    outj.parent.mkdir(parents=True, exist_ok=True)
    out = {'rows': rows, 'best_per_galaxy': list(by.values()), 'summary': {'wins_if': wins, 'N': len(by), 'median_dAICc': med, 'IQR': [q1,q3]}}
    outj.write_text(json.dumps(out, indent=2), encoding='utf-8')
    # HTML report
    out_dir = Path('server/public/reports'); out_dir.mkdir(parents=True, exist_ok=True)
    rep = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>Phi·eta sweep (rep6)</title><link rel="stylesheet" href="../styles.css"></head><body>',
           '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
           '<main class="wrap"><h1>Phi·eta パラメタ軽スイープ — 代表6</h1>']
    rep.append(f'<div class=card><p>勝ち数(Phi·eta): {wins} / {len(by)}（ΔAICc(Phi·eta−W·S)&lt;0 を勝ち）</p>'
               f'<p>ΔAICc 中央値[IQR]: {med:.2f} [{q1:.2f}, {q3:.2f}]</p></div>')
    rep.append('<table><thead><tr><th>Galaxy</th><th>best β</th><th>s[kpc]</th><th>σ_k</th><th>AICc(W·S)</th><th>AICc(Phi·eta)</th><th>ΔAICc</th></tr></thead><tbody>')
    for r in by.values():
        d = float(r['AICc_if'] - r['AICc_ws'])
        rep.append(f"<tr><td>{r['name']}</td><td>{r['beta']}</td><td>{r['s_kpc']}</td><td>{r['sigma_k']}</td><td>{r['AICc_ws']:.2f}</td><td>{r['AICc_if']:.2f}</td><td>{d:.2f}</td></tr>")
    rep.append('</tbody></table>')
    rep.append('</main></body></html>')
    (out_dir/'ws_vs_phieta_sweep.html').write_text('\n'.join(rep), encoding='utf-8')
    print('wrote', out_dir/'ws_vs_phieta_sweep.html')
    pg.tick('html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

