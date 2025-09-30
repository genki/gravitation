#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple


def parse_stamp_name(p: Path) -> Tuple[str, float, float, float]:
    """Extract (stamp, se, psf, hp) from filename pattern '<stamp>_se-<se>_psf-<psf>_hp-<hp>.json'."""
    name = p.stem  # without .json
    # drop optional suffixes like '.html'
    for suf in ('.html', '.json'):
        if name.endswith(suf):
            name = name[: -len(suf)]
    parts = name.split('_')
    stamp = parts[0] if parts else ''
    se = ''
    psf = float('nan')
    hp = float('nan')
    for token in parts:
        if token.startswith('se-'):
            se = token[3:]
        elif token.startswith('psf-'):
            try:
                psf = float(token[4:])
            except Exception:
                psf = float('nan')
        elif token.startswith('hp-'):
            try:
                hp = float(token[3:])
            except Exception:
                hp = float('nan')
    return stamp, se, psf, hp


def load_rows(dirpath: Path) -> List[dict]:
    rows: List[dict] = []
    for p in sorted(dirpath.glob('*.json')):
        try:
            j = json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            continue
        stamp, se, psf, hp = parse_stamp_name(p)
        # pull metrics if present
        s = j.get('S_shadow') or j.get('indicators', {}).get('S_shadow') or {}
        perm = s.get('perm') or {}
        sval = (s.get('values') or {}).get('global')
        p_perm = perm.get('p_perm_one_sided_pos')
        delta = j.get('delta') or {}
        d_shift = delta.get('FDB_minus_shift')
        rows.append({
            'stamp': stamp,
            'se': se,
            'psf': psf,
            'hp': hp,
            'S_shadow': float(sval) if isinstance(sval, (int, float)) else float('nan'),
            'p_perm': float(p_perm) if isinstance(p_perm, (int, float)) else float('nan'),
            'delta_shift': float(d_shift) if isinstance(d_shift, (int, float)) else float('nan'),
            'path': str(p.name),
        })
    return rows


def render_html(holdout: str, rows: List[dict]) -> str:
    head = (
        '<html lang="ja-JP"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>{holdout} A‑4 FAST サマリ</title><link rel="stylesheet" href="../styles.css">'
        '</head><body><header class="site-header"><div class="wrap">'
        '<div class="brand">研究進捗</div><nav class="nav">'
        '<a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a>'
        '</nav></div></header><main class="wrap">'
        f'<h1>{holdout} — A‑4 FAST（Σ変換×PSF×高通過）</h1>'
    )
    body = ['<div class=card><table class="t">'
            '<thead><tr><th>stamp</th><th>se</th><th>psf</th><th>hp</th>'
            '<th>S_shadow(global)</th><th>p_perm(>0)</th><th>ΔAICc(FDB−shift)</th><th>JSON</th></tr></thead><tbody>']
    # order by p_perm ascending (smaller is better), then by S_shadow desc
    rows_sorted = sorted(rows, key=lambda r: (r['p_perm'] if r['p_perm'] == r['p_perm'] else 1.0, - (r['S_shadow'] if r['S_shadow'] == r['S_shadow'] else -1e9)))
    for r in rows_sorted:
        body.append(
            '<tr>'
            f"<td>{r['stamp']}</td><td>{r['se']}</td><td>{r['psf']}</td><td>{r['hp']}</td>"
            f"<td>{r['S_shadow']:.3f}</td><td>{r['p_perm']:.3g}</td><td>{r['delta_shift']:.1f}</td>"
            f"<td><a href='a4_fast/{holdout}/{r['path']}'>json</a></td>"
            '</tr>'
        )
    body.append('</tbody></table></div>')
    tail = '</main></body></html>'
    return head + '\n'.join(body) + tail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--holdout', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    src = Path('server/public/reports/a4_fast') / args.holdout
    src.mkdir(parents=True, exist_ok=True)
    rows = load_rows(src)
    outp = Path(args.out)
    outp.write_text(render_html(args.holdout, rows), encoding='utf-8')
    print(f'wrote {outp}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

