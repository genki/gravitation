#!/usr/bin/env python3
from __future__ import annotations
import re
import requests
from pathlib import Path
from typing import List, Dict


def sesame_identifiers(name: str) -> Dict[str, List[str]]:
    url = f"https://cds.u-strasbg.fr/cgi-bin/nph-sesame/-oI/A?{name}"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    main: List[str] = []
    alias: List[str] = []
    for ln in r.text.splitlines():
        if ln.startswith('%I '):
            s = ln[3:].strip()
            if s and s not in main:
                main.append(s)
        elif ln.startswith('%I.'):
            s = ln.split(' ', 1)[1].strip() if ' ' in ln else ''
            if s and s not in alias:
                alias.append(s)
    return {'main': main, 'alias': alias}


def update_memo(name: str, ids: Dict[str, List[str]]) -> None:
    p = Path('memo/galaxies') / f"{name}.md"
    if not p.exists():
        return
    s = p.read_text(encoding='utf-8')
    lines = s.splitlines()
    # build section text
    sect = ["## 識別子 (Sesame/SIMBAD)"]
    if ids['main']:
        sect.append("- 主要: " + ", ".join(ids['main']))
    if ids['alias']:
        sect.append("- 別名: " + ", ".join(ids['alias'][:10]) + (" …" if len(ids['alias'])>10 else ""))
    sect.append("")
    body = "\n".join(sect)
    # insert before 参考リンク or at end
    inserted = False
    out: List[str] = []
    i = 0
    while i < len(lines):
        if not inserted and lines[i].strip() == '## 参考リンク':
            out.append(body)
            inserted = True
        out.append(lines[i])
        i += 1
    if not inserted:
        out.append(body)
    p.write_text("\n".join(out) + "\n", encoding='utf-8')


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='*', default=['CamB'])
    args = ap.parse_args()
    for nm in args.names:
        try:
            ids = sesame_identifiers(nm)
            update_memo(nm, ids)
            print('updated ids for', nm, ids['main'][:1])
        except Exception as e:
            print('warn: failed for', nm, e)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

