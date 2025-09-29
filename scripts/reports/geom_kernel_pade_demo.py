#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from theory.pade_kernels import pade_disk_gR, disk_true_gR


def main() -> int:
    a = 5.0  # kpc
    eps = 0.8
    R = np.geomspace(0.05*a, 10*a, 200)
    gt = disk_true_gR(R, a=a, eps=eps)
    gp = pade_disk_gR(R, a=a, eps=eps)
    # relative error
    rel = np.where(np.abs(gt) > 1e-12, np.abs((gp-gt)/gt), np.nan)
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    # plots
    fig, ax = plt.subplots(1,1, figsize=(5.6,3.6))
    ax.loglog(R/a, np.abs(gt)+1e-12, label='true')
    ax.loglog(R/a, np.abs(gp)+1e-12, '--', label='Padé [2/2] (初期)')
    ax.set_xlabel('R/a'); ax.set_ylabel('|g_R| (arb.)'); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(outdir/'disk_kernel_gr_compare.png', dpi=140); plt.close(fig)

    fig, ax = plt.subplots(1,1, figsize=(5.6,3.6))
    ax.semilogx(R/a, rel)
    ax.set_xlabel('R/a'); ax.set_ylabel('相対誤差')
    ax.set_title('均一円盤: 近似誤差（初期係数）')
    fig.tight_layout(); fig.savefig(outdir/'disk_kernel_gr_error.png', dpi=140); plt.close(fig)

    # HTML
    html = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>幾何カーネル Padé 近似（円盤）</title><link rel="stylesheet" href="../styles.css"></head><body>',
            '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
            '<main class="wrap"><h1>有限ディスクの 1/r カーネル近似（Padé 雛形）</h1>',
            '<div class=card><p>Padé [2/2]の初期係数での真値比較と相対誤差。係数最適化は今後のステップ。</p></div>',
            '<div class=card><img src="disk_kernel_gr_compare.png" style="max-width:100%"></div>',
            '<div class=card><img src="disk_kernel_gr_error.png" style="max-width:100%"></div>',
            '</main></body></html>']
    (outdir/'geom_kernel_pade_disk.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote', outdir/'geom_kernel_pade_disk.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

