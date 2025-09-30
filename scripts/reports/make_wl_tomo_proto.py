#!/usr/bin/env python3
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np
from astropy.cosmology import FlatLambdaCDM
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.reports.make_cosmo_formal import CosmologyConfig, compute_wl_predictions


REPO = Path(__file__).resolve().parents[2]
NZ_DIR = REPO / 'data' / 'weak_lensing' / 'kids450_release' / 'KiDS-450_COSMIC_SHEAR_DATA_RELEASE' / 'Nz_CC'


@dataclass
class TomoBin:
    name: str
    z: np.ndarray
    nz: np.ndarray
    z_eff: float


def load_nz_bins() -> List[TomoBin]:
    bins: List[TomoBin] = []
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
            z_eff = float(np.trapz(z * nz_norm, z)) if s > 0 else float(np.nan)
            bins.append(TomoBin(name=p.name, z=z, nz=nz_norm, z_eff=z_eff))
        except Exception:
            continue
    return bins


def main() -> int:
    out_dir = REPO / 'server/public/state_of_the_art'
    out_dir.mkdir(parents=True, exist_ok=True)
    cfg = CosmologyConfig()
    tomo = load_nz_bins()
    if not tomo:
        page = '<html lang="ja-JP"><meta charset="utf-8"><title>WL tomo proto</title><body><main class="wrap"><h1>WLトモグラフィ（KiDS-450）— 準備中</h1><div class=card><p>n(z) ファイルが見つかりません。fetch スクリプトで配布物を展開してください。</p></div></main></body></html>'
        (out_dir / 'wl_2pcf_tomo_proto.html').write_text(page, encoding='utf-8')
        print('wrote wl_2pcf_tomo_proto.html (no n(z) found)')
        return 0

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    axes = axes.ravel()
    rows: List[str] = []
    for i, tb in enumerate(tomo[:4]):  # 4ビンまで描画
        ax = axes[i]
        # 近似: n(z)→delta(z_eff) として compute_wl_predictions に供給
        pred = compute_wl_predictions('lcdm', cfg, z_source=max(tb.z_eff, 0.2))
        th = pred['theta_arcmin']
        ax.plot(th, pred['xi_plus'], label='ξ⁺(LCDM)')
        ax.plot(th, pred['xi_minus'], label='ξ⁻(LCDM)')
        ax.set_title(f'{tb.name} (z_eff≈{tb.z_eff:.2f})')
        ax.set_xscale('log'); ax.set_yscale('log')
        ax.set_xlabel('θ [arcmin]'); ax.set_ylabel('ξ±')
        ax.grid(True, ls=':', alpha=0.4)
        if i == 0:
            ax.legend(frameon=False, fontsize=8)
        rows.append(f'<tr><td>{tb.name}</td><td>{tb.z_eff:.3f}</td><td>{len(tb.z)}</td></tr>')

    png = out_dir / 'wl_tomo_proto.png'
    fig.suptitle('WL 2PCF（KiDS-450）トモグラフィ予測（proto; z_eff 近似）', fontsize=12)
    fig.savefig(png, dpi=150); plt.close(fig)

    html = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>WL 2PCF（KiDS-450）トモグラフィ（proto）</title><link rel="stylesheet" href="../styles.css"></head><body>',
            '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
            '<main class="wrap"><h1>WL 2PCF（KiDS-450）トモグラフィ（proto）</h1>',
            '<div class=card><p>配布 n(z)（Nz_CC）から z_eff を推定し、各ビンの ξ± を LCDM 近似で描画（Late‑FDB も後続で追加予定）。現段階では χ²/AICc は算出せず、図示のみ。</p></div>',
            f'<div class=card><img src="wl_tomo_proto.png" style="max-width:100%"></div>',
            '<div class=card><h3>n(z) 要約</h3><table class="t"><thead><tr><th>bin</th><th>z_eff</th><th>samples</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table></div>",
            '</main></body></html>']
    (out_dir / 'wl_2pcf_tomo_proto.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote wl_2pcf_tomo_proto.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

