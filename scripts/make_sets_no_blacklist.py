#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
from typing import List, Set


def load_names(p: Path) -> List[str]:
    return [ln.strip() for ln in p.read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.strip().startswith('#')]


def load_bl(p: Path) -> Set[str]:
    s: Set[str] = set()
    if not p.exists():
        return s
    for ln in p.read_text(encoding='utf-8').splitlines():
        t = ln.strip()
        if t and not t.startswith('#'):
            s.add(t.split(',', 1)[0].strip())
    return s


def main() -> int:
    sets = Path('data/sparc/sets')
    bl = load_bl(sets / 'blacklist.txt')
    for name in ['lsb.txt', 'hsb.txt']:
        src = sets / name
        if not src.exists():
            print('skip missing', src)
            continue
        arr = [nm for nm in load_names(src) if nm not in bl]
        out = sets / (src.stem + '_noBL.txt')
        out.write_text('\n'.join(arr) + '\n', encoding='utf-8')
        print('wrote', out, f'({len(arr)})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

