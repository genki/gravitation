#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

try:
    # Japanese/CJK glyphs if available
    from scripts.utils.mpl_fonts import use_jp_font as _use_jp_font
    _use_jp_font()
except Exception:
    pass

from scripts.figs.io_rep6 import load_observed, load_model


COLORS = {
    'OBS': 'black',
    'GR': '#7f7f7f',
    'GRDM': '#7b2cbf',
    'MOND': '#2a9d8f',
    'FDB_WS': '#d62828',
    'FDB_IF': '#1d4ed8',
}


def _g_and_err(R: np.ndarray, V: np.ndarray, eV: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    Rm = np.maximum(R, 1e-6)
    g = (V * V) / Rm
    eg = 2.0 * V * np.maximum(eV, 1e-6) / Rm
    return g, eg


def _outer_gr2_slope(R: np.ndarray, V: np.ndarray) -> Tuple[float, Tuple[float,float]]:
    """Return slope of g(R)*R^2 over outer 30% radii and an approximate 95% CI.
    Simple OLS with normal approximation; robust enough for quick diagnostics.
    """
    Rm = np.maximum(R, 1e-6)
    g = (V * V) / Rm
    y = g * (Rm ** 2)
    thr = np.nanquantile(Rm[np.isfinite(Rm)], 0.70)
    m = np.isfinite(Rm) & np.isfinite(y) & (Rm >= thr)
    if not np.any(m):
        return float('nan'), (float('nan'), float('nan'))
    x = Rm[m]
    yy = y[m]
    X = np.vstack([x, np.ones_like(x)]).T
    beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
    slope = float(beta[0])
    # CI via residual SE
    yhat = X @ beta
    resid = yy - yhat
    dof = max(len(yy) - 2, 1)
    s2 = float(np.sum(resid**2)) / dof
    Sxx = float(np.sum((x - np.mean(x))**2))
    se = math.sqrt(s2 / max(Sxx, 1e-12))
    ci = (slope - 1.96*se, slope + 1.96*se)
    return slope, ci


def make_page(name: str) -> Dict:
    obs = load_observed(name)
    models = ['GR', 'GRDM', 'MOND', 'FDB_WS', 'FDB_IF']
    results: Dict[str, Dict] = {}
    for m in models:
        try:
            results[m] = load_model(name, m)
        except Exception as e:
            results[m] = {'error': str(e), 'meta': {}}

    # Baseline FDB_WS for residuals
    V_base = results['FDB_WS']['V_total'] if 'V_total' in results.get('FDB_WS', {}) else np.zeros_like(obs.V)
    resid = obs.V - V_base

    # Outer slope on baseline model total
    slope, ci = _outer_gr2_slope(obs.R, V_base)

    # Plot
    fig = plt.figure(figsize=(8.6, 6.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[3.0, 1.4], hspace=0.15)
    ax = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0], sharex=ax)

    # Observations
    ax.errorbar(obs.R, obs.V, yerr=np.maximum(obs.eV, 1e-6), fmt='o', color=COLORS['OBS'], ms=3, lw=0.8, alpha=0.9, label='観測')

    # Lines
    order = ['GR', 'GRDM', 'MOND', 'FDB_WS', 'FDB_IF']
    for m in order:
        dat = results.get(m) or {}
        Vt = dat.get('V_total')
        if Vt is None:
            continue
        ax.plot(obs.R, Vt, color=COLORS[m], lw=2.2 if m.startswith('FDB') else 1.8, label=f'{m} Total')
        # FDB addition as dashed
        if m.startswith('FDB') and dat.get('V_add') is not None:
            ax.plot(obs.R, dat['V_add'], color=COLORS[m], lw=1.2, ls='--', alpha=0.8, label=f'{m} 追加')

    ax.set_ylabel('速度 [km/s]')
    ax.grid(True, ls=':', alpha=0.5)
    ax.legend(loc='best', fontsize=8, ncol=2)

    ax2.axhline(0.0, color='#555', lw=0.8)
    ax2.plot(obs.R, resid, color=COLORS['FDB_WS'], lw=1.2)
    ax2.set_xlabel('半径 R [kpc]')
    ax2.set_ylabel('残差 [km/s]')
    ax2.grid(True, ls=':', alpha=0.5)

    # Caption/footnote block
    meta = {m: (results[m].get('meta') or {}) for m in order}
    N = int(meta['FDB_WS'].get('N') or meta['GR'].get('N') or len(obs.R))
    k_ws = int(meta['FDB_WS'].get('k') or 2)
    aic_ws = meta['FDB_WS'].get('AICc')
    r_ws = meta['FDB_WS'].get('rchi2')
    d_if = float((meta['FDB_IF'].get('AICc') or np.nan) - (aic_ws or np.nan))
    d_grdm = float((meta['GRDM'].get('AICc') or np.nan) - (aic_ws or np.nan))
    d_mond = float((meta['MOND'].get('AICc') or np.nan) - (aic_ws or np.nan))

    foot = (
        f"N={N}, k={k_ws}, rχ²={r_ws:.3f} (FDB‑W·S), "
        f"AICc(FDB‑W·S)={aic_ws:.1f}, ΔAICc(IF/GRDM/MOND)="
        f"{d_if:+.1f}/{d_grdm:+.1f}/{d_mond:+.1f}; "
        f"外縁 d[gR²]/dR ≈ {slope:.2g} (95%CI [{ci[0]:.2g},{ci[1]:.2g}])"
    )
    fig.suptitle(f'{name} — 統一テンプレ v2（Total=太線/追加=破線）', fontsize=12)
    fig.text(0.02, 0.01, foot, fontsize=8)

    # Save
    out_dir = Path('server/public/reports')
    out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / f'bench_{name.lower()}.png'
    svg = out_dir / f'bench_{name.lower()}.svg'
    try:
        from matplotlib import rcParams
        rcParams['svg.fonttype'] = 'none'
    except Exception:
        pass
    fig.tight_layout(rect=[0,0.04,1,0.96])
    fig.savefig(png, dpi=150)
    fig.savefig(svg)
    plt.close(fig)

    # HTML page
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>Bench: {name}</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        f'<main class="wrap"><h1>{name} — 統一テンプレ v2（Total=太線/追加=破線）</h1>',
        '<div class="card">', f'<p><img src="bench_{name.lower()}.png" style="max-width:100%"></p>', f'<p><small>{foot}</small></p>', '</div>'
    ]
    # Mini-table
    def r(x):
        return 'nan' if x is None or (isinstance(x, float) and (not np.isfinite(x))) else f'{x:.3f}' if isinstance(x, float) else str(x)
    rows = []
    for key, lab, k in [('GR','GR',1), ('GRDM','GR+DM',3), ('MOND','MOND',1), ('FDB_WS','FDB‑W·S',2), ('FDB_IF','FDB‑Φ·η',2)]:
        mm = meta.get(key,{})
        rows.append(f"<tr><td>{lab}</td><td>{int(mm.get('N',N))}</td><td>{int(mm.get('k',k))}</td>"
                    f"<td>{float(mm.get('AICc',float('nan'))):.1f}</td><td>{float(mm.get('rchi2',float('nan'))):.3f}</td>" 
                    f"<td>{float(mm.get('chi2',float('nan'))):.1f}</td></tr>")
    html.append('<div class=card><h3>統計（AICc / rχ² / χ²）</h3>'
                '<table class="t"><thead><tr><th>model</th><th>N</th><th>k</th><th>AICc</th><th>rχ²</th><th>χ²</th></tr></thead>'
                f"<tbody>{''.join(rows)}</tbody></table></div>")
    html.append('</main></body></html>')
    page = out_dir / f'bench_{name.lower()}.html'
    page.write_text('\n'.join(html), encoding='utf-8')

    # JSON summary for audits
    out_json = out_dir / f'bench_{name.lower()}.json'
    summary = {
        'name': name,
        'meta': meta,
        'outer_slope': {'slope': slope, 'ci95': {'low': ci[0], 'high': ci[1]}},
        'figures': {'png': str(png), 'svg': str(svg)},
    }
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description='Single-galaxy bench report (rep6 template v2)')
    ap.add_argument('--name', required=True, help='galaxy name, e.g., UGC06787')
    args = ap.parse_args()
    make_page(args.name)
    print('wrote', f'server/public/reports/bench_{args.name.lower()}.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

