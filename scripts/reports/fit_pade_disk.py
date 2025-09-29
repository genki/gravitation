#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from theory.pade_kernels import disk_true_gR


def pade_disk(R: np.ndarray, a: float, coeffs: tuple[float,float,float,float,float]) -> np.ndarray:
    c0, c1, c2, d1, d2 = coeffs
    x = np.asarray(R, float) / max(a, 1e-12)
    num = c0 + c1*x + c2*x*x
    den = 1.0 + d1*x + d2*x*x
    return (x * num / np.maximum(den, 1e-12)) * (1.0 / max(a, 1e-12))


def rel_err(gt: np.ndarray, gp: np.ndarray) -> float:
    m = np.isfinite(gt) & np.isfinite(gp) & (np.abs(gt) > 1e-12)
    if not np.any(m):
        return np.inf
    re = np.abs((gp[m]-gt[m]) / gt[m])
    # robust: median + 95p tail penalty
    return float(np.nanmedian(re) + 0.5*np.nanpercentile(re, 95))


def grid_optimize(a: float, eps: float) -> tuple[tuple[float,...], float]:
    # coarse-to-fine grid around initial guess
    R = np.geomspace(0.05*a, 10*a, 300)
    gt = disk_true_gR(R, a=a, eps=eps)
    best = ((1.0, 0.1, -0.05, 0.7, 0.15), 1e9)
    grids = [
        (np.linspace(0.6, 1.4, 7), np.linspace(-0.2, 0.4, 7), np.linspace(-0.3, 0.1, 7), np.linspace(0.2, 1.2, 7), np.linspace(0.0, 0.4, 7)),
        (np.linspace(0.8, 1.2, 7), np.linspace(-0.1, 0.2, 7), np.linspace(-0.15, -0.0, 7), np.linspace(0.4, 1.0, 7), np.linspace(0.05, 0.25, 7)),
    ]
    for grid in grids:
        c0s, c1s, c2s, d1s, d2s = grid
        for c0 in c0s:
            for c1 in c1s:
                for c2 in c2s:
                    for d1 in d1s:
                        for d2 in d2s:
                            gp = pade_disk(R, a, (c0,c1,c2,d1,d2))
                            e = rel_err(gt, gp)
                            if e < best[1]:
                                best = ((c0,c1,c2,d1,d2), e)
        # refine around current best
        c0,c1,c2,d1,d2 = best[0]
        def ring(x, r):
            return np.linspace(max(x-r, -2.0), min(x+r, 2.0), 7)
        grids = [ (ring(c0, 0.2), ring(c1, 0.1), ring(c2, 0.1), ring(d1, 0.2), ring(d2, 0.1)) ]
    return best


def main() -> int:
    a = 5.0; eps = 0.8
    coeffs, err = grid_optimize(a, eps)
    R = np.geomspace(0.05*a, 10*a, 400)
    gt = disk_true_gR(R, a=a, eps=eps)
    gp = pade_disk(R, a, coeffs)
    re = np.where(np.abs(gt)>1e-12, np.abs((gp-gt)/gt), np.nan)
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1,1, figsize=(5.6,3.6))
    ax.loglog(R/a, np.abs(gt)+1e-12, label='true')
    ax.loglog(R/a, np.abs(gp)+1e-12, '--', label=f'Padé opt (med+0.5*95p≈{err:.3f})')
    ax.set_xlabel('R/a'); ax.set_ylabel('|g_R| (arb.)'); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(outdir/'disk_kernel_gr_compare_opt.png', dpi=140); plt.close(fig)
    fig, ax = plt.subplots(1,1, figsize=(5.6,3.6))
    ax.semilogx(R/a, re)
    ax.set_xlabel('R/a'); ax.set_ylabel('相対誤差')
    ax.set_title('均一円盤: 近似誤差（最適化後）')
    fig.tight_layout(); fig.savefig(outdir/'disk_kernel_gr_error_opt.png', dpi=140); plt.close(fig)
    # HTML
    html = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>Padé近似（円盤; 最適化）</title><link rel="stylesheet" href="../styles.css"></head><body>',
            '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
            '<main class="wrap"><h1>有限ディスクの 1/r カーネル近似（Padé; 最適化）</h1>',
            f'<div class=card><p>最適係数: c0={coeffs[0]:.3f}, c1={coeffs[1]:.3f}, c2={coeffs[2]:.3f}, d1={coeffs[3]:.3f}, d2={coeffs[4]:.3f}</p>'
            f'<p><small>目的関数: median(|δ|)+0.5×p95(|δ|)。eps={eps}, a={a}kpc。</small></p></div>',
            '<div class=card><img src="disk_kernel_gr_compare_opt.png" style="max-width:100%"></div>',
            '<div class=card><img src="disk_kernel_gr_error_opt.png" style="max-width:100%"></div>',
            '</main></body></html>']
    (outdir/'geom_kernel_pade_disk_opt.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote', outdir/'geom_kernel_pade_disk_opt.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

