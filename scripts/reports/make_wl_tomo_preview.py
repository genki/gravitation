#!/usr/bin/env python3
from __future__ import annotations

"""WL 2PCF tomographic preview using n(z) per bin (no covariance).

Outputs a preview HTML under server/public/state_of_the_art/wl_2pcf_tomo_preview.html
with per-bin predicted ξ± for ΛCDM and Late‑FDB.
"""

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.reports.make_cosmo_formal import CosmologyConfig, compute_wl_predictions


REPO = Path(__file__).resolve().parents[2]
NZ_DIR = REPO / 'data' / 'weak_lensing' / 'kids450_release' / 'KiDS-450_COSMIC_SHEAR_DATA_RELEASE' / 'Nz_CC'


@dataclass
class BinNZ:
    name: str
    z: np.ndarray
    nz: np.ndarray
    z_eff: float


def load_bins() -> List[BinNZ]:
    bins: List[BinNZ] = []
    if not NZ_DIR.exists():
        return bins
    for p in sorted(NZ_DIR.glob('Nz_CC_*.asc')):
        try:
            arr = np.loadtxt(p)
            if arr.ndim != 2 or arr.shape[1] < 2:
                continue
            z = arr[:, 0].astype(float)
            nz = arr[:, 1].astype(float)
            nz = np.clip(nz, 0.0, None)
            s = float(np.trapz(nz, z))
            if s > 0:
                nz_norm = nz / s
            else:
                nz_norm = nz
            z_eff = float(np.trapz(z * nz_norm, z)) if s > 0 else float('nan')
            bins.append(BinNZ(name=p.name, z=z, nz=nz_norm, z_eff=z_eff))
        except Exception:
            continue
    return bins


def main() -> int:
    out_dir = REPO / 'server/public/state_of_the_art'
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = CosmologyConfig()
    bins = load_bins()
    if not bins:
        page = '<html lang="ja-JP"><meta charset="utf-8"><title>WL tomo preview</title><body><main class="wrap"><h1>WLトモグラフィ（KiDS‑450）— n(z) 未配置</h1><div class=card><p>Nz_CC が見つかりません。fetch スクリプトで配布物を展開してください。</p></div></main></body></html>'
        (out_dir / 'wl_2pcf_tomo_preview.html').write_text(page, encoding='utf-8')
        print('wrote wl_2pcf_tomo_preview.html (no n(z))')
        return 0

    figs: List[str] = []
    for i, b in enumerate(bins[:4], 1):
        nz_pair = (b.z, b.nz)
        pred_l = compute_wl_predictions('lcdm', cfg, z_source=None, nz_pair=nz_pair)
        pred_f = compute_wl_predictions('late_fdb', cfg, z_source=None, nz_pair=nz_pair)

        th = pred_l['theta_arcmin']
        fig, ax = plt.subplots(figsize=(4.8, 3.2))
        ax.plot(th, pred_l['xi_plus'], label='ξ⁺ LCDM', color='gray')
        ax.plot(th, pred_l['xi_minus'], label='ξ⁻ LCDM', color='silver')
        ax.plot(th, pred_f['xi_plus'], label='ξ⁺ Late‑FDB', color='darkblue')
        ax.plot(th, pred_f['xi_minus'], label='ξ⁻ Late‑FDB', color='royalblue')
        ax.set_xscale('log'); ax.set_yscale('log')
        ax.set_xlabel('θ [arcmin]'); ax.set_ylabel('ξ±')
        ax.set_title(f'{b.name} (z_eff≈{b.z_eff:.2f})')
        ax.grid(True, ls=':', alpha=0.4)
        if i == 1:
            ax.legend(frameon=False, fontsize=8)
        png = out_dir / f'wl_tomo_preview_bin{i}.png'
        fig.tight_layout(); fig.savefig(png, dpi=150); plt.close(fig)
        figs.append(png.name)

    rows = ''.join([f'<tr><td>{b.name}</td><td>{b.z_eff:.3f}</td><td>{len(b.z)}</td></tr>' for b in bins[:4]])
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>WL 2PCF（KiDS-450）トモグラフィ（preview）</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>WL 2PCF（KiDS-450）トモグラフィ（preview; n(z)畳み込み）</h1>',
        '<div class=card><p>各トモグラフィビンの n(z) を用いて ξ± を予測（ΛCDM / Late‑FDB）。共分散・IA/m補正は未適用のプレビュー版。</p></div>',
    ]
    for i, fn in enumerate(figs, 1):
        html.append(f'<div class=card><h3>bin{i}</h3><p><img src="{fn}" style="max-width:100%"></p></div>')
    html.append('<div class=card><h3>n(z) 要約</h3><table class="t"><thead><tr><th>bin</th><th>z_eff</th><th>samples</th></tr></thead>'
                f'<tbody>{rows}</tbody></table></div>')
    html.append('</main></body></html>')
    (out_dir / 'wl_2pcf_tomo_preview.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote wl_2pcf_tomo_preview.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

