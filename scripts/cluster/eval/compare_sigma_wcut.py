#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from astropy.io import fits
from typing import Tuple
import numpy as np


def _center_crop_to_common(a: np.ndarray, b: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    ha, wa = a.shape; hb, wb = b.shape
    h = min(ha, hb); w = min(wa, wb)
    def crop(x):
        H, W = x.shape
        cy, cx = H//2, W//2
        y0 = max(0, cy - h//2); x0 = max(0, cx - w//2)
        return x[y0:y0+h, x0:x0+w]
    return crop(a), crop(b)


def rel_diff(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        a, b = _center_crop_to_common(a, b)
    m = np.isfinite(a) & np.isfinite(b)
    if not np.any(m):
        return float('nan')
    # robust median relative difference
    denom = np.maximum(np.abs(b[m]), 1e-12)
    r = np.abs(a[m] - b[m]) / denom
    return float(np.nanmedian(r))


def main() -> int:
    name = 'Bullet'
    root = Path(f'data/cluster/{name}')
    out = Path('server/public/reports'); out.mkdir(parents=True, exist_ok=True)
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>CIAO モザイク差分</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>Bullet: CIAO正式モザイク 差分チェック</h1>'
    ]
    cur_sig = root/'sigma_e.fits'; cur_w = root/'omega_cut.fits'
    new_sig = root/'sigma_e_ciao.fits'; new_w = root/'omega_cut_ciao.fits'
    if not (cur_sig.exists() and cur_w.exists()):
        html.append('<div class=card><p>現行 sigma_e/omega_cut が見つかりません。</p></div>')
    ok = True
    if new_sig.exists():
        rs = rel_diff(fits.getdata(new_sig).astype(float), fits.getdata(cur_sig).astype(float))
        html.append(f'<div class=card><p>sigma_e: 中央相対差 = {rs:.3g}</p></div>')
        ok = ok and (rs < 0.1)
    else:
        html.append('<div class=card><p>sigma_e_ciao.fits が未生成（CIAO 実行未了）。</p></div>')
        ok = False
    if new_w.exists():
        rw = rel_diff(fits.getdata(new_w).astype(float), fits.getdata(cur_w).astype(float))
        html.append(f'<div class=card><p>omega_cut: 中央相対差 = {rw:.3g}</p></div>')
        ok = ok and (rw < 0.1)
    else:
        html.append('<div class=card><p>omega_cut_ciao.fits が未生成（CIAO 実行未了）。</p></div>')
        ok = False
    if ok:
        html.append('<div class=card><p><b>PASS</b>: 差分 < 10% で安定です。</p></div>')
    else:
        html.append('<div class=card><p><b>PENDING</b>: CIAO 実行が未完了、または差分が閾値以上。</p>'
                    '<p><small>実行例: <code>bash scripts/cluster/cxo/build_sigma_wcut_ciao.sh Bullet 0.5:2.0</code></small></p></div>')
    html.append('</main></body></html>')
    (out/'bullet_ciao_diff.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out/'bullet_ciao_diff.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
