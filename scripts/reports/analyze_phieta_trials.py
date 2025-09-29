#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np


def main() -> int:
    trials = Path('data/results/ws_vs_phieta_trials.ndjson')
    if not trials.exists():
        print('no trials file:', trials)
        return 0
    rows = []
    with trials.open('r', encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                r = json.loads(ln)
                if isinstance(r, dict) and r.get('ok'): rows.append(r)
            except Exception:
                pass
    if not rows:
        print('no valid rows')
        return 0
    # Group by galaxy
    by_g = {}
    for r in rows:
        by_g.setdefault(r['name'], []).append(r)
    # Build HTML
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    html = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>Phi·eta: ΔAICc ヒット集計</title><link rel="stylesheet" href="../styles.css"></head><body>',
            '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
            '<main class="wrap"><h1>Phi·eta スイープ — ΔAICc ヒット（閾値: −6）</h1>']
    total_hits = 0
    for g, arr in by_g.items():
        arr2 = [r for r in arr if float(r.get('delta', 1e9)) <= -6.0]
        total_hits += len(arr2)
        if not arr2:
            html.append(f'<h2>{g}</h2><div class=card><p><small>ヒット無し（ΔAICc≤−6 未達）</small></p></div>')
            continue
        arr2.sort(key=lambda r: float(r['delta']))
        best = arr2[0]
        med = float(np.median([float(r['delta']) for r in arr2]))
        iqr = float(np.subtract(*np.percentile([float(r['delta']) for r in arr2], [75,25])))
        html.append(f'<h2>{g}</h2>')
        html.append('<div class=card>')
        html.append(f'<p>ヒット数: {len(arr2)} / {len(arr)}（best ΔAICc={best["delta"]:.2f}, β={best["beta"]:.2f}, s={best["s_kpc"]:.2f}, σ_k={best["sgk"]:.2f})</p>')
        html.append(f'<p>ΔAICc ヒットの中央値[IQR]: {med:.2f} [{iqr:.2f}]</p>')
        html.append('</div>')
        # Table of top 10
        html.append('<table><thead><tr><th>β</th><th>s[kpc]</th><th>σ_k</th><th>ΔAICc</th></tr></thead><tbody>')
        for r in arr2[:10]:
            html.append(f'<tr><td>{r["beta"]:.2f}</td><td>{r["s_kpc"]:.2f}</td><td>{r["sgk"]:.2f}</td><td>{r["delta"]:.2f}</td></tr>')
        html.append('</tbody></table>')
    if total_hits == 0:
        html.append('<div class=card><p><small>閾値ヒットはまだありません。スイープ継続中です。</small></p></div>')
    html.append('</main></body></html>')
    out = outdir / 'phieta_hits.html'
    out.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

