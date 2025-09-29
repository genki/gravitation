#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path


def main() -> int:
    rep_dir = Path('server/public/reports')
    out = rep_dir / 'benchmarks' / 'index.html'
    out.parent.mkdir(parents=True, exist_ok=True)
    items = []
    for p in sorted(rep_dir.glob('bench_*.html')):
        name = p.stem.replace('bench_', '').upper()
        items.append((name, p))
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>単一銀河ベンチマーク</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>単一銀河ベンチマーク（FDB≡h‑only＋界面Σ, DMなし）</h1>',
        '<p>固定 μ0(k)・同一n/誤差/ペナルティで GR/GR+DM/MOND/FDB を横並び評価。各銀河の統計・図は下記リンクから。</p>'
    ]
    if not items:
        html.append('<div class=card><p>ベンチページがまだありません。</p></div>')
    else:
        html.append('<section class="two-col">')
        for name, p in items:
            rel = f'../{p.name}'
            html.append(f'<figure class="card"><figcaption><a href="{rel}">{name}</a></figcaption></figure>')
        html.append('</section>')
    html.append('</main></body></html>')
    out.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

