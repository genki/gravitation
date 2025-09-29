#!/usr/bin/env python3
from __future__ import annotations
import math, json, subprocess as sp
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font


def aicc(AIC: float, k: int, N: int) -> float:
    return float(AIC) + (2.0 * int(k) * (int(k) + 1)) / max(int(N) - int(k) - 1, 1)


def run_one(err_floor_kms: float, eps_mult: float) -> tuple[float, float]:
    # surface mode on NGC3198 with line-eps as H_cut surrogate
    out = Path(f'data/results/ngc3198_sense_e{err_floor_kms:.0f}_m{eps_mult:.2f}.json')
    args = [
        'PYTHONPATH=.', './.venv/bin/python', 'scripts/compare_fit_multi.py',
        '--names-file', 'data/sparc/sets/ngc3198_only.txt', '--fdb-mode', 'surface',
        '--pad-factor', '2', '--inv1-orth', '--robust', 'huber',
        '--err-floor-kms', f'{err_floor_kms:.3f}', '--line-eps', f'{0.8*eps_mult:.3f}',
        '--out', str(out),
    ]
    sp.run(' '.join(args), shell=True, check=True)
    d = json.loads(out.read_text(encoding='utf-8'))
    A = float(d['AIC']['ULW']); N = int(d['N_total']['ULW']); k = int(d['AIC']['k']['ULW'])
    chi = float(d['chi2_total']['ULW'])
    return aicc(A, k, N), (chi / max(N - k, 1))


def main() -> int:
    use_jp_font()
    floors = [3.0, 5.0, 7.0]
    mults = [0.5, 1.0, 1.5]
    labels = []
    AICcs = []
    rchis = []
    for f in floors:
        for m in mults:
            a, r = run_one(f, m)
            labels.append(f'f{int(f)}_m{m:.1f}')
            AICcs.append(a)
            rchis.append(r)
    # normalize to min=best for radar plot (lower is better)
    A = np.array(AICcs); R = np.array(rchis)
    A_n = (A.max() - A) / (A.max() - A.min() + 1e-9)
    R_n = (R.max() - R) / (R.max() - R.min() + 1e-9)
    theta = np.linspace(0, 2*np.pi, len(labels)+1)
    A_plot = np.r_[A_n, A_n[0]]
    R_plot = np.r_[R_n, R_n[0]]
    fig, ax = plt.subplots(1,1, subplot_kw={'projection':'polar'}, figsize=(6,6))
    ax.plot(theta, A_plot, label='AICc（規格化，高いほど良）', lw=2.0)
    ax.fill(theta, A_plot, alpha=0.15)
    ax.plot(theta, R_plot, label='rχ²（規格化，高いほど良）', lw=2.0)
    ax.set_xticks(theta[:-1])
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title('NGC 3198 — 誤差床/薄層幅（H_cut代替）感度（スパイダー図）')
    ax.legend(loc='lower left', bbox_to_anchor=(0.05, -0.05), fontsize=9)
    out_png = Path('server/public/reports/sensitivity_ngc3198.png')
    fig.tight_layout(); fig.savefig(out_png, dpi=140, bbox_inches='tight'); plt.close(fig)
    # Compute best region (ΔAICc≤2) and best combo
    A = np.array(AICcs)
    A_best = float(A.min())
    best_idx = int(A.argmin())
    best_label = labels[best_idx]
    within2 = [lab for lab, a in zip(labels, AICcs) if (a - A_best) <= 2.0]
    # HTML wrapper
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>感度解析（NGC 3198）</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>誤差床・H_cut感度（NGC 3198）</h1>',
        '<div class=card><p>誤差床 f∈{3,5,7} km/s と薄層幅 ε∈{0.5,1.0,1.5}× 基準に対する AICc と rχ² の安定性を図示。値は最良=1 に正規化。</p>'
        f'<p><small>最適（AICc最小）: {best_label}。許容域（ΔAICc≤2）: {", ".join(within2) if within2 else "—"}</small></p></div>',
        f'<div class=card><p><img src="sensitivity_ngc3198.png" style="max-width:100%"></p></div>',
        '</main></body></html>'
    ]
    (Path('server/public/reports')/'sensitivity_ngc3198.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out_png)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
