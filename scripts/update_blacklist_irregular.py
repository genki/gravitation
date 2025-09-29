#!/usr/bin/env python3
from __future__ import annotations
"""
SPARCのTable1を用いて形態型が不規則(=Im)の銀河を検出し、
data/sparc/sets/blacklist.txt に追記する（重複は抑止）。

基準:
  - T指数が >= 10 のもの（Table1のIm/BCD相当）
  - （予防的）名前ベースの例外は現時点では無し
"""
from pathlib import Path
from typing import List, Set
from scripts.fit_sparc_fdbl import read_sparc_meta


def load_names(p: Path) -> List[str]:
    if not p.exists():
        return []
    return [
        ln.strip() for ln in p.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith('#')
    ]


def main() -> int:
    sets = Path('data/sparc/sets')
    all_names = sets / 'all.txt'
    table1 = Path('data/sparc/SPARC_Lelli2016c.mrt')
    bl = sets / 'blacklist.txt'

    names = load_names(all_names)
    irregular: List[str] = []
    for nm in names:
        m = read_sparc_meta(table1, nm)
        try:
            t = getattr(m, 'T', None)
        except Exception:
            t = None
        if isinstance(t, int) and t >= 10:
            irregular.append(nm)

    # load existing blacklist names
    already: Set[str] = set()
    if bl.exists():
        for ln in bl.read_text(encoding='utf-8').splitlines():
            s = ln.strip()
            if s and not s.startswith('#'):
                already.add(s.split(',', 1)[0].strip())

    # append
    added = 0
    lines: List[str] = []
    if not bl.exists():
        lines.append('# 自動検出により強い外的要因の可能性が高いもの')
    for nm in irregular:
        if nm not in already:
            lines.append(f"{nm},morph:Irregular")
            added += 1
    if lines:
        bl.parent.mkdir(parents=True, exist_ok=True)
        with bl.open('a', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    print(f'irregular found={len(irregular)}, appended={added} to {bl}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

