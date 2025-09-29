#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any


REPO = Path(__file__).resolve().parents[2]
SRC = REPO / 'server/public/reports/cluster'
DST = REPO / 'server/public/state_of_the_art/holdout_progress.html'


def load_json(p: Path) -> Dict[str, Any] | None:
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return None


def fmt(v: float | int | None, digits: int = 3) -> str:
    try:
        if v is None:
            return '—'
        if isinstance(v, int):
            return str(v)
        return f"{float(v):.{digits}f}"
    except Exception:
        return '—'


def row_for(name: str) -> str:
    p = SRC / f'{name}_holdout.json'
    j = load_json(p)
    if not j:
        return f'<tr><td>{name}</td><td colspan=6><small>no data</small></td></tr>'
    a = j.get('AICc', {})
    d = j.get('delta', {})
    s = (j.get('indicators', {}) or {}).get('S_shadow') or {}
    s_val = (s.get('values') or {}).get('global', s.get('global'))
    perm = (s.get('perm') or {})
    p_perm = perm.get('p_perm_one_sided_pos')
    n_perm = perm.get('n')
    d_rot = d.get('FDB_minus_rot', a.get('FDB', float('nan')) - a.get('rot', float('nan')))
    d_shift = d.get('FDB_minus_shift', a.get('FDB', float('nan')) - a.get('shift', float('nan')))
    return (
        f'<tr><td>{name}</td>'
        f'<td>{fmt(a.get("FDB"))}</td><td>{fmt(a.get("rot"))}</td><td>{fmt(a.get("shift"))}</td>'
        f'<td>{fmt(d_rot)}</td><td>{fmt(d_shift)}</td>'
        f'<td>{fmt(s_val)}</td><td>{fmt(p_perm)}</td><td>{fmt(n_perm,0)}</td></tr>'
    )


def main() -> int:
    names = ['MACSJ0416', 'AbellS1063']
    rows = [row_for(n) for n in names]
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>HO進捗（MACSJ0416 / AbellS1063）</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>ホールドアウト進捗（MACSJ0416 / AbellS1063）</h1>',
        '<div class=card><table class="t"><thead><tr><th>Holdout</th><th>AICc(FDB)</th><th>AICc(rot)</th><th>AICc(shift)</th><th>Δ(FDB−rot)</th><th>Δ(FDB−shift)</th><th>S_shadow</th><th>p_perm</th><th>n</th></tr></thead><tbody>',
        '\n'.join(rows),
        '</tbody></table><p><small>注: 進行中のFAST/FULLにより随時更新されます（rng=42固定）。</small></p></div>',
        '</main></body></html>'
    ]
    DST.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', DST)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

