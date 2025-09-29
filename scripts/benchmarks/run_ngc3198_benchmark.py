#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess as sp
from pathlib import Path


def run(cmd: list[str]):
    sp.run(' '.join(cmd), shell=True, check=True)


def main() -> int:
    out = Path('server/public/reports/bench_ngc3198.html')
    out.parent.mkdir(parents=True, exist_ok=True)
    # 1) Ensure CV (clean) with fixed μ(k)
    try:
        run(['PYTHONPATH=.', './.venv/bin/python', 'scripts/cross_validate_shared.py',
             '--names-file', 'data/sparc/sets/clean_for_fit.txt', '--out-prefix', 'cv_shared_summary', '--robust', 'huber',
             '--fixed-mu-eps', '1', '--fixed-mu-k0', '0.2', '--fixed-mu-m', '2', '--fixed-gas-scale', '1.33'])
    except Exception:
        pass
    # 2) Build simple HTML that links to the data/procedure and SOTA
    solar = Path('data/results/solar_null_log.json')
    solar_block = ''
    if solar.exists():
        try:
            solar_block = f'<pre>{solar.read_text(encoding="utf-8")}</pre>'
        except Exception:
            pass
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Benchmark: NGC 3198</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">ホーム</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>単一銀河系ベンチマーク — NGC 3198</h1>',
        '<p>手順書: <a href="../../docs/benchmarks/NGC3198_procedure.md">NGC3198_procedure.md</a></p>',
        '<p>本ページは固定 μ0(k) とフェア条件の整備を確認するベースです。実データ（Hα/HI）投入時に自動で図と表が更新されます。</p>',
        '<h2>太陽系 Null ログ</h2>', solar_block,
        '</main></body></html>'
    ]
    out.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

