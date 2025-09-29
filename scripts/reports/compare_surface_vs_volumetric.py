#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess as sp, hashlib
from pathlib import Path

# Reuse model builders so that per‑galaxy stats are correct
from scripts.compare_fit_multi import (
    read_sparc_massmodels,
    model_ulw_accel,
    line_bias_accel,
    to_accel,
    chi2,
)
from scripts.utils.progress import ProgressETA


def run_mode(names_file: Path, mode: str, out_json: Path) -> dict:
    args = [
        'PYTHONPATH=.', './.venv/bin/python', 'scripts/compare_fit_multi.py',
        '--names-file', str(names_file), '--fdb-mode', mode,
        '--pad-factor', '2', '--eg-frac-floor', '0.15', '--inv1-orth', '--line-eps', '0.8',
        '--out', str(out_json),
    ]
    sp.run(' '.join(args), shell=True, check=True)
    return json.loads(out_json.read_text(encoding='utf-8'))


def aicc_from_chi(chi: float, k: int, N: int) -> float:
    return float(chi) + 2*int(k) + (2*int(k)*(int(k)+1)) / max(int(N)-int(k)-1, 1)


def per_gal_metrics(payload: dict, mode: str) -> dict:
    """Compute per‑galaxy chi², N, k for the given compare_fit_multi result.

    mode: 'surface' or 'ulw' (volumetric)
    """
    res = {}
    mrt = Path('data/sparc/MassModels_Lelli2016c.mrt')
    lam = float(payload.get('lam'))
    A = float(payload.get('A'))
    gas_scale = float(payload.get('gas_scale', 1.0))
    mus = payload.get('mu', {}).get('ULW', {})  # per‑galaxy μ chosen in that run
    for nm in payload.get('names', []):
        rc = read_sparc_massmodels(mrt, nm)
        R = rc.R
        # Apply consistent error model: floor dV (km/s) and fractional floor in accel
        import numpy as _np
        Vobs = rc.Vobs
        eV0 = _np.maximum(rc.eV, 1e-6)
        floor = _np.clip(0.03 * _np.abs(Vobs), 3.0, 7.0)  # km/s
        eVe = _np.sqrt(eV0 * eV0 + floor * floor)
        Rm = _np.maximum(R, 1e-6)
        g_obs = (Vobs * Vobs) / Rm
        eg = 2.0 * Vobs * _np.maximum(eVe, 1e-6) / Rm
        # additional fractional/absolute floor in accel space to match site policy
        eg = _np.sqrt(eg * eg + (0.15 * g_obs) ** 2 + (0.0 ** 2))
        g_gas = gas_scale * (rc.Vgas*rc.Vgas) / (R.clip(min=1e-6))
        g_star = (rc.Vdisk*rc.Vdisk + rc.Vbul*rc.Vbul) / (R.clip(min=1e-6))
        mu = float((mus.get(nm, {}) or {}).get('mu', 0.7))
        if mode == 'surface':
            g_ulw_unit = line_bias_accel(R, rc.SBdisk, pix_kpc=0.2, size=256, line_eps_kpc=0.8, pad_factor=2)
            g_ulw = A * g_ulw_unit
        else:
            g_ulw = model_ulw_accel(R, rc.SBdisk, lam_kpc=lam, A=A, pix_kpc=0.2, size=256,
                                   boost=0.5, s1_kpc=lam/8.0, s2_kpc=lam/3.0, pad_factor=2)
        g_model = g_gas + mu * g_star + g_ulw
        c = chi2(g_obs, eg, g_model)
        N = int((~(~(g_obs==g_obs) | ~(eg==eg) | ~(g_model==g_model))).sum())  # fallback mask; replaced below
        # robust N count with finite mask
        import numpy as _np
        m = _np.isfinite(g_obs) & _np.isfinite(eg) & _np.isfinite(g_model)
        N = int(_np.sum(m))
        k = 1  # per‑galaxy degree (μ)
        res[nm] = {'chi2': float(c), 'N': N, 'k': k}
    return res


def md5sum(p: Path) -> str:
    try:
        return hashlib.md5(p.read_bytes()).hexdigest()[:12]
    except Exception:
        return ''


def main() -> int:
    names = Path('data/sparc/sets/rep6.txt')
    pg = ProgressETA([
        ('run_surface', 3),
        ('run_volumetric', 3),
        ('per_gal_metrics', 3),
        ('html', 1),
    ])
    pg.start(total_hint_min=5.0)
    out_dir = Path('server/public/reports'); out_dir.mkdir(parents=True, exist_ok=True)
    surf = run_mode(names, 'surface', Path('data/results/rep6_surface.json'))
    pg.tick('run_surface')
    volm = run_mode(names, 'ulw',     Path('data/results/rep6_volumetric.json'))
    pg.tick('run_volumetric')
    ms = per_gal_metrics(surf, 'surface')
    mv = per_gal_metrics(volm, 'ulw')
    pg.tick('per_gal_metrics')

    rep = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
           '<title>Surface vs Volumetric (rep6)</title><link rel="stylesheet" href="../styles.css"></head><body>',
           '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
           '<main class="wrap"><h1>Σ（界面） vs 体積版（ULM）— 代表6銀河</h1>']
    # Quick links to bench/A/B for high-visibility galaxies
    rep.append('<div class="card pill-links"><p>Quick Links: '
               '<a href="bench_ngc2403.html">bench NGC2403</a>'
               '<a href="bench_ngc3198.html">bench NGC3198</a>'
               '<a href="ws_vs_phieta_fair.html">A/B (W·S vs Φ×η)</a></p></div>')
    rep.append(('<div class=card><small>AICc, rχ² は per‑galaxy (N,k) で算出。names: rep6.txt '
               f'/ script=compare_surface_vs_volumetric.py (md5:{md5sum(Path(__file__))})'
               f' / names(md5:{md5sum(names)})'
               '</small></div>'))
    # Definition of thin layer and normals (requested clarity)
    rep.append('<div class=card><small>定義: ω_cut ∝ √n_e, 層幅 ε ≃ H_cut = |∇ln ω_cut|^{-1}, 法線 n ∝ −∇ω_cut。ULM‑D(=面) は界面 Σ に沿う、ULM‑P(=体積) は体積核で評価。</small></div>')
    rep.append('<table><thead><tr>'
               '<th>Galaxy</th><th>AICc (Surface)</th><th>rχ² (Surface)</th>'
               '<th>AICc (Volumetric/ULM)</th><th>rχ² (Volumetric/ULM)</th>'
               '<th>N</th><th>k</th><th>ΔAICc (S−V)</th><th>ΔELPD≈−0.5Δχ²</th><th>links</th></tr></thead><tbody>')
    wins_s = wins_v = 0
    deltas = []
    import math
    for nm in surf.get('names', []):
        s = ms[nm]; v = mv[nm]
        a_s = aicc_from_chi(s['chi2'], s['k'], s['N'])
        a_v = aicc_from_chi(v['chi2'], v['k'], v['N'])
        r_s = (s['chi2'] / max(s['N'] - s['k'], 1))
        r_v = (v['chi2'] / max(v['N'] - v['k'], 1))
        d = a_s - a_v
        deltas.append(d)
        if d < 0: wins_s += 1
        elif d > 0: wins_v += 1
        delpd = -0.5 * (s['chi2'] - v['chi2'])
        fair = 'ws_vs_phieta_fair.html'
        prof = f'{nm.lower()}_phieta_profile.html'
        bench = f'bench_{nm.lower()}.html'
        link = f'<a href="{fair}">A/B</a>'
        from pathlib import Path as _P
        if (_P('server/public/reports')/prof).exists():
            link += f' · <a href="{prof}">profile</a>'
        if (_P('server/public/reports')/bench).exists():
            link += f' · <a href="{bench}">bench</a>'
        ji = f'{nm.lower()}_JI_vector_panel.html'
        if (_P('server/public/reports')/ji).exists():
            link += f' · <a href="{ji}">JI vector</a>'
        loc = f'{nm.lower()}_local_stability.html'
        if (_P('server/public/reports')/loc).exists():
            link += f' · <a href="{loc}">local stability</a>'
        oss = f'{nm.lower()}_outer_slope_stability.html'
        if (_P('server/public/reports')/oss).exists():
            link += f' · <a href="{oss}">outer slope</a>'
        # Tooltip with reproducibility meta and policy (uid_md5 defined above if file exists)
        try:
            _uid = uid_md5
        except Exception:
            _uid = ''
        tip = (f"誤差床: dV_floor=clip(0.03×|Vobs|,3..7) km/s; seed=fixed; "
               f"names md5={md5sum(names)}; used_ids md5={_uid}")
        # Winner badge (ΔAICc S−V; green if surface wins)
        badge = '<span class="kpi-light green"></span>' if d < 0 else '<span class="kpi-light red"></span>'
        rep.append(f'<tr><td title="{tip}">{badge} {nm}</td><td>{a_s:.1f}</td><td>{r_s:.2f}</td>'
                   f'<td>{a_v:.1f}</td><td>{r_v:.2f}</td><td>{s["N"]}</td><td>{s["k"]}</td><td>{d:.1f}</td><td>{delpd:.1f}</td><td>{link}</td></tr>')
    rep.append('</tbody></table>')
    # Aggregate summaries: win rate and ΔAICc median/IQR
    try:
        import numpy as _np
        d_arr = _np.array(deltas, dtype=float)
        med = float(_np.nanmedian(d_arr))
        q1, q3 = float(_np.nanpercentile(d_arr, 25)), float(_np.nanpercentile(d_arr, 75))
        iqr = q3 - q1
    except Exception:
        med = float('nan'); iqr = float('nan')
    total = max(wins_s + wins_v, 1)
    win_rate_surface = wins_s / total
    rep.append(f'<div class=card><p>勝ち数: Surface={wins_s} / Volumetric={wins_v} '
               f'(勝率 Surface={win_rate_surface:.2f})</p>'
               f'<p>ΔAICc(S−V) 中央値[IQR]: {med:.1f} [{iqr:.1f}]</p>'
               '<p><small>誤差モデル: dV_floor=clip(0.03×Vobs, 3..7) km/s, eg=2V·dV/R, eg_frac_floor=0.15 を両方式に適用。'
               ' per‑galaxy 自由度 k=1（Υ★）。勝率は ΔAICc<0（Surface優位）の割合。'
               ' ΔAICc は Surface−Volumetric（負なら Surface 優位）。</small></p></div>')
    # Violin/box plot for ΔAICc distribution
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as _plt
        fig, ax = _plt.subplots(1,1, figsize=(5.8,3.6))
        ax.violinplot(d_arr, showmeans=True, showmedians=True)
        ax.boxplot(d_arr, vert=True, widths=0.2, positions=[1.0])
        ax.axhline(0.0, color='0.5', ls='--', lw=1.0)
        ax.set_xticks([1.0]); ax.set_xticklabels(['ΔAICc(S−V)'])
        ax.set_ylabel('ΔAICc'); ax.set_title('代表6: ΔAICc 分布')
        png = out_dir / 'rep6_delta_violin.png'
        fig.tight_layout(); fig.savefig(png, dpi=140); _plt.close(fig)
        rep.append(f'<div class=card><img src="rep6_delta_violin.png" style="max-width:100%"></div>')
    except Exception:
        pass
    # Repro meta: script/name hashes, dataset version (used_ids.csv) and seed policy
    try:
        uid = Path('server/public/state_of_the_art/used_ids.csv')
        uid_md5 = md5sum(uid) if uid.exists() else ''
    except Exception:
        uid_md5 = ''
    rep.append('<div class=card><small>'
               f'script md5: compare_surface_vs_volumetric.py={md5sum(Path(__file__))}; names={md5sum(names)}; '
               f'used_ids.csv md5={uid_md5}; seed=fixed where applicable; error-floor policy as上記。</small></div>')
    # Footnote: result JSON hashes
    rep.append('<div class=card><small>'
               f'result md5: surface={md5sum(Path("data/results/rep6_surface.json"))}, '
               f'volumetric={md5sum(Path("data/results/rep6_volumetric.json"))}</small></div>')
    rep.append('</main></body></html>')
    (out_dir/'surface_vs_volumetric.html').write_text('\n'.join(rep), encoding='utf-8')
    print('wrote', out_dir/'surface_vs_volumetric.html')
    pg.tick('html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
