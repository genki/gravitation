#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import os
import re
from typing import List


def build_grid(img_dir: Path, names: List[str], base_dir: Path, cols: int = 2) -> str:
    # two columns x three rows grid
    items = []
    for nm in names:
        # pick PNG if available, otherwise SVG
        png = img_dir / f'{nm}_rep6.png'
        svg = img_dir / f'{nm}_rep6.svg'
        img = png if png.exists() else svg
        meta = img.with_suffix('.json') if img.suffix.lower() == '.png' else png.with_suffix('.json')
        caption = nm
        if meta.exists():
            try:
                j = json.loads(meta.read_text(encoding='utf-8'))
                b = j.get('baseline', {})
                da = j.get('dAICc', {})
                caption = f"{nm} — N={b.get('N')} k={b.get('k')} AICc={b.get('AICc'):.1f} ΔAICc(IF/GRDM/MOND)={da.get('FDB_IF', float('nan')):+.1f}/{da.get('GRDM', float('nan')):+.1f}/{da.get('MOND', float('nan')):+.1f}"
            except Exception:
                pass
        # Build web-root path under server/public/assets/rep6 to avoid climbing out of static root
        web_img = Path('server/public/assets/rep6') / img.name
        rel = os.path.relpath(web_img, start=base_dir)
        items.append(f'<figure style="margin:6px">\n<img src="{rel}" alt="{nm} rep6">\n<figcaption><small>{caption}</small></figcaption>\n</figure>')
    # wrap in a simple grid container
    css = '<style>.rep6-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;}</style>'
    html = ['<!-- REP6_FIGS_BEGIN -->', css, '<div class="rep6-grid">'] + items + ['</div>', '<!-- REP6_FIGS_END -->']
    return '\n'.join(html)


def main() -> int:
    ap = argparse.ArgumentParser(description='Inject rep6 figures into the HTML report')
    ap.add_argument('--in', dest='inp', required=True, help='input HTML path')
    ap.add_argument('--imgs', required=True, help='directory containing rep6 images')
    ap.add_argument('--grid', default='2x3', help='grid shape (unused; fixed 2x3)')
    args = ap.parse_args()
    inp = Path(args.inp)
    img_dir = Path(args.imgs)
    names = [ln.strip() for ln in Path('data/sparc/sets/rep6.txt').read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.startswith('#')]
    grid_html = build_grid(img_dir, names, base_dir=inp.parent, cols=2)
    txt = inp.read_text(encoding='utf-8') if inp.exists() else ''
    begin = '<!-- REP6_FIGS_BEGIN -->'
    end = '<!-- REP6_FIGS_END -->'
    heading = '<h2>代表比較図（テンプレv2, Total基準）</h2>'
    if begin in txt and end in txt:
        out = re.sub(r'<!-- REP6_FIGS_BEGIN -->.*?<!-- REP6_FIGS_END -->', grid_html, txt, count=1, flags=re.DOTALL)
    else:
        # Clean up any legacy injected blocks (without markers) heuristically
        pattern = r'<h2>代表比較図（テンプレv2, Total基準）</h2>\s*(<style>.*?</style>\s*)?<div class="rep6-grid">.*?</div>'
        cleaned = re.sub(pattern, '', txt, flags=re.DOTALL)
        anchor = '</table>'
        if anchor in cleaned:
            out = cleaned.replace(anchor, anchor + '\n' + heading + '\n' + grid_html)
        else:
            out = cleaned + '\n' + heading + '\n' + grid_html
    inp.write_text(out, encoding='utf-8')
    print('injected 6 figures into', inp)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
