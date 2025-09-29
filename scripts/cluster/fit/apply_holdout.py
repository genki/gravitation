#!/usr/bin/env python3
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
import subprocess


def main() -> int:
    params = Path('data/cluster/params_cluster.json')
    if not params.exists():
        print('error: missing shared params; run fit/global_fit.py')
        return 1
    P = json.loads(params.read_text(encoding='utf-8'))
    # Build W,S with shared params (alpha,beta fixed via file)
    subprocess.run(['bash', '-lc', 'PYTHONPATH=. ./.venv/bin/python scripts/cluster/fdb/make_S_W.py'], check=False)
    subprocess.run(['bash', '-lc', 'PYTHONPATH=. ./.venv/bin/python scripts/cluster/fdb/kappa_fdb.py'], check=False)
    # Compose kappa_tot = kappa_GR(baryon) + kappa_FDB (GR(baryon) placeholder=0 until maps available)
    kappa_fdb = np.load('data/cluster/fdb/bullet_kappa_fdb.npy')
    # build GR(baryon) proxy
    try:
        from scripts.cluster.gr.kappa_baryon import main as build_gr
        build_gr()
        kappa_gr = np.load('data/cluster/gr/bullet_kappa_gr.npy')
        if kappa_gr.shape != kappa_fdb.shape:
            import scipy.ndimage as ndi
            zy, zx = kappa_fdb.shape[0]/kappa_gr.shape[0], kappa_fdb.shape[1]/kappa_gr.shape[1]
            kappa_gr = ndi.zoom(kappa_gr, zoom=(zy, zx), order=1)
    except Exception:
        kappa_gr = np.zeros_like(kappa_fdb)
    kappa_tot = kappa_gr + kappa_fdb
    out_dir = Path('server/public/reports/cluster'); out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / 'bullet_kappa_tot.npy', kappa_tot)
    # quicklook HTML
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(9, 3))
    ax[0].imshow(kappa_gr, cmap='magma'); ax[0].set_title('κ_GR(baryon)')
    ax[1].imshow(kappa_fdb, cmap='viridis'); ax[1].set_title('κ_FDB')
    ax[2].imshow(kappa_tot, cmap='plasma'); ax[2].set_title('κ_tot')
    for a in ax: a.axis('off')
    fig.tight_layout(); png = out_dir / 'bullet_kappa_panels.png'; fig.savefig(png, dpi=140); plt.close(fig)
    html = Path('server/public/reports/cluster/bullet_overview.html')
    html.write_text('<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<title>バレットクラスタ — FDB(ULM) 薄レンズ近似</title><link rel="stylesheet" href="../styles.css"></head><body>'
                    '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div>'
                    '<nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav>'
                    '</div></header><main class="wrap"><h1>バレットクラスタ — FDB(ULM) 薄レンズ近似（共有パラ固定）</h1>'
                    f'<div class=card><p><img src="{png.name}" style="max-width:100%"></p>'
                    f'<p><small>params_cluster.json: {Path("data/cluster/params_cluster.json").read_text(encoding="utf-8")}</small></p></div>'
                    '</main></body></html>', encoding='utf-8')
    print('wrote', html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
