#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.fit_sparc_fdbl import read_sparc_massmodels
from scripts.compare_fit_multi import compute_inv1_unit


def outer_slope(R: np.ndarray, g_obs: np.ndarray, frac_start: float = 0.7) -> tuple[float, float]:
    x = R
    y = g_obs * (R.clip(min=1e-6))
    n = len(x); start = int(max(0, n*frac_start))
    xs = x[start:]; ys = y[start:]
    if len(xs) < 3:
        return float('nan'), float('nan')
    xs0 = xs - xs.mean()
    Sxx = float((xs0*xs0).sum())
    a = float((xs0*ys).sum() / max(Sxx,1e-12))
    b = float(ys.mean())
    yhat = a*xs0 + b
    rss = float(((ys - yhat)**2).sum()); dof = max(len(xs)-2,1)
    sigma2 = rss / dof
    se_a = (sigma2 / max(Sxx,1e-12))**0.5
    return a, 1.96*se_a


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='Outer 1/r^2 slope stability via Jackknife & Bootstrap')
    ap.add_argument('--name', required=True)
    args = ap.parse_args()
    nm = args.name
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), nm)
    R = rc.R
    g_obs = (rc.Vobs*rc.Vobs) / np.clip(R, 1e-6, None)
    # Jackknife over start fraction
    fracs = np.linspace(0.6, 0.85, 11)
    slopes = []; ci95 = []
    for f in fracs:
        a, ci = outer_slope(R, g_obs, frac_start=float(f))
        slopes.append(a); ci95.append(ci)
    # Bootstrap of outer bins (last 30%)
    n = len(R); start = int(max(0, n*0.7))
    xs = R[start:]; ys = g_obs[start:] * R[start:]
    if len(xs) >= 3:
        rng = np.random.default_rng(2025)
        bs = []
        for _ in range(500):
            idx = rng.integers(0, len(xs), len(xs))
            x = xs[idx]; y = ys[idx]
            x0 = x - x.mean(); Sxx = float((x0*x0).sum());
            a = float((x0*y).sum() / max(Sxx,1e-12))
            bs.append(a)
        bs = np.array(bs)
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    else:
        lo = hi = np.nan
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1,1, figsize=(6.0,4.0))
    ax.plot(fracs, slopes, '-o', label='slope')
    ax.fill_between(fracs, np.array(slopes)-np.array(ci95), np.array(slopes)+np.array(ci95), color='C0', alpha=0.2, label='±95% (linfit)')
    if np.isfinite(lo) and np.isfinite(hi):
        ax.axhspan(lo, hi, color='C3', alpha=0.15, label='Bootstrap 95% (outer 30%)')
    ax.axhline(0.0, color='0.5', ls='--', lw=1.0)
    ax.set_xlabel('start fraction for outer fit'); ax.set_ylabel('slope of g·R²'); ax.legend(frameon=False)
    ax.set_title(f'{nm}: 外縁 1/r² 傾きの安定性')
    png = outdir / f'{nm.lower()}_outer_slope_stability.png'
    fig.tight_layout(); fig.savefig(png, dpi=140); plt.close(fig)
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{nm}: 外縁 1/r² 傾きの安定性</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        f'<main class="wrap"><h1>{nm}: 外縁 1/r² 傾き（Jackknife/Bootstrap）</h1>',
        f'<div class=card><img src="{png.name}" style="max-width:100%"></div>',
        '</main></body></html>'
    ]
    (outdir / f'{nm.lower()}_outer_slope_stability.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote', outdir / f'{nm.lower()}_outer_slope_stability.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

