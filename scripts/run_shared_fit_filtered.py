#!/usr/bin/env python3
from __future__ import annotations
import subprocess as sp
from pathlib import Path
from typing import List, Set


def load_names(p: Path) -> List[str]:
    if not p.exists():
        return []
    return [
        ln.strip() for ln in p.read_text(encoding='utf-8').splitlines()
        if ln.strip() and not ln.strip().startswith('#')
    ]


def load_setfile(p: Path) -> Set[str]:
    return set(load_names(p))


def main() -> int:
    base = Path('data/sparc/sets')
    # prefer clean_for_fit if present; fall back to all.txt
    base_names = base / 'clean_for_fit.txt'
    if not base_names.exists():
        base_names = base / 'all.txt'
    names = load_names(base_names)
    if not names:
        raise SystemExit(f'no names found in {base_names}')
    # subtract blacklist and manual exclude
    bl = load_setfile(base / 'blacklist.txt')
    ex = load_setfile(base / 'exclude_env.txt')
    filt = [nm for nm in names if nm not in bl and nm not in ex]
    # write tmp names file for reproducibility
    out_names = base / 'clean_no_blacklist.txt'
    out_names.write_text('\n'.join(filt) + '\n', encoding='utf-8')
    print(f'kept {len(filt)} / {len(names)} (blacklist={len(bl)}, manual_exclude={len(ex)}) -> {out_names}')

    # run shared-params fit on filtered set (moderate grid for speed)
    out_json = Path('data/results/multi_fit_all_noBL.json')
    cmd = [
        'PYTHONPATH=.', './.venv/bin/python', 'scripts/compare_fit_multi.py',
        '--names-file', str(out_names),
        '--boost', '0.5', '--boost-tie-lam', '--auto-geo',
        '--pad-factor', '2', '--eg-frac-floor', '0.15', '--inv1-orth', '--line-eps', '0.8',
        '--gas-scale-grid', '1.0,1.33',
        '--lam-grid', '15,18,20,24',
        '--A-grid', '80,100,125',
        '--out', str(out_json),
    ]
    sp.run(' '.join(cmd), shell=True, check=True)

    # build HTML report
    out_html = Path('server/public/reports/multi_fit_all_noBL.html')
    sp.run(['PYTHONPATH=.', './.venv/bin/python', 'scripts/build_report.py'], check=False)
    print(f'built JSON: {out_json}\nHTML report: {out_html}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

