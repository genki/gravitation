#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests


WIKI_EN = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
WIKI_JA = "https://ja.wikipedia.org/api/rest_v1/page/summary/{}"


def load_names(p: Path) -> List[str]:
    return [ln.strip() for ln in p.read_text(encoding='utf-8').splitlines()
            if ln.strip() and not ln.strip().startswith('#')]


def wiki_title_for(name: str) -> str:
    s = name.strip()
    m = re.match(r"^(NGC|UGC|IC|ESO|DDO|UGCA|KK|KKH|KKs)\s*-?\s*(.+)$", s, re.I)
    if m:
        return (m.group(1).upper() + " " + m.group(2)).replace(' ', '_')
    return s.replace(' ', '_')


def fetch_wiki(name: str) -> Tuple[Optional[Dict], Optional[str]]:
    # Try English first, then Japanese
    for base in (WIKI_EN, WIKI_JA):
        url = base.format(wiki_title_for(name))
        try:
            r = requests.get(
                url, timeout=20,
                headers={
                    'User-Agent': 'gravitation-research-bot/0.1 (+https://localhost)'
                },
            )
            if r.status_code == 200:
                return r.json(), url
        except Exception:
            pass
    return None, None


FLAG_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("interacting", re.compile(r"\binteract(ing|ion)\b|tidal|companion|merger|collisional|ram pressure", re.I)),
    ("AGN/starburst", re.compile(r"AGN|Seyfert|LINER|starburst", re.I)),
    ("bar/warp/ring", re.compile(r"barred|warped|polar ring|ring galaxy", re.I)),
    ("cluster/group", re.compile(r"cluster|group|subgroup|satellite galaxy", re.I)),
]


def analyze_text(text: str) -> List[str]:
    flags = []
    for tag, pat in FLAG_PATTERNS:
        if pat.search(text or ""):
            flags.append(tag)
    return flags


def write_memo(outdir: Path, name: str, info: Dict, url: Optional[str], flags: List[str]) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    title = info.get('title') if info else name
    desc = (info or {}).get('description', '') or ''
    extract = (info or {}).get('extract', '') or ''
    content_url = (info or {}).get('content_urls', {}).get('desktop', {}).get('page')
    url = url or content_url
    md = []
    md.append(f"# {title}（自動調査メモ）")
    md.append("")
    # Prepare research links, will be appended at the bottom
    q = requests.utils.quote(name)
    links = {
        'Wikipedia(en)': f'https://en.wikipedia.org/wiki/{q}',
        'Wikipedia(ja)': f'https://ja.wikipedia.org/wiki/{q}',
        'NED by name': f'https://ned.ipac.caltech.edu/byname?objname={q}',
        'SIMBAD': f'https://simbad.u-strasbg.fr/simbad/sim-id?Ident={q}',
        'ADS': f'https://ui.adsabs.harvard.edu/search/q={q}&sort=date%20desc',
        'arXiv': f'https://arxiv.org/search/?query={q}&searchtype=all&order=-announced_date_first',
        'Google Scholar': f'https://scholar.google.com/scholar?q={q}',
    }
    md.append("## 概要")
    if desc:
        md.append(f"- 要約: {desc}")
    if url:
        md.append(f"- 参照: {url}")
    md.append("")
    if extract:
        md.append("## 抜粋")
        md.append(extract.strip())
        md.append("")
    md.append("## 外的要因/特記事項 推定")
    if flags:
        md.append("- 兆候: " + ", ".join(flags))
    else:
        md.append("- 兆候: 特に検出なし（要目視確認）")
    md.append("")
    md.append("## 追加メモ（手動追記用）")
    md.append("- 相互作用/伴銀河:")
    md.append("- バー/ワープ/リング:")
    md.append("- 活動銀河核/スターバースト:")
    md.append("- グループ/クラスタ所属:")
    md.append("")
    # Append links at the bottom
    md.append('## 参考リンク')
    for label, href in links.items():
        md.append(f'- [{label}]({href})')
    md.append("")
    (outdir / f"{name}.md").write_text("\n".join(md) + "\n", encoding='utf-8')


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--names-file', type=Path, default=Path('data/sparc/sets/nearby.txt'))
    ap.add_argument('--outdir', type=Path, default=Path('memo/galaxies'))
    ap.add_argument('--blacklist', type=Path, default=Path('data/sparc/sets/blacklist.txt'))
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--sleep', type=float, default=0.7, help='秒; 連続アクセスの礼儀')
    args = ap.parse_args()

    names = load_names(args.names_file)
    if args.limit and args.limit > 0:
        names = names[: args.limit]

    bl: List[Tuple[str, str]] = []
    index: Dict[str, Dict] = {}
    # load existing index (accumulate across chunked runs)
    if (args.outdir / 'index.json').exists():
        try:
            index = json.loads((args.outdir / 'index.json').read_text(encoding='utf-8'))
        except Exception:
            index = {}
    for i, nm in enumerate(names, 1):
        info, src = fetch_wiki(nm)
        extract = (info or {}).get('extract', '') or ''
        desc = (info or {}).get('description', '') or ''
        text = f"{desc}\n{extract}"
        flags = analyze_text(text)
        write_memo(args.outdir, nm, info or {}, src, flags)
        index[nm] = {
            'src': src, 'flags': flags,
            'title': (info or {}).get('title'),
            'description': (info or {}).get('description'),
        }
        if any(tag in flags for tag in ("interacting", "AGN/starburst")):
            bl.append((nm, ";".join(flags)))
        time.sleep(max(args.sleep, 0.0))

    # write index and blacklist (append unique)
    (args.outdir / 'index.json').write_text(json.dumps(index, indent=2), encoding='utf-8')
    args.blacklist.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if args.blacklist.exists():
        for ln in args.blacklist.read_text(encoding='utf-8').splitlines():
            s = ln.strip()
            if s and not s.startswith('#'):
                existing.add(s.split(',')[0])
    lines = []
    if not args.blacklist.exists():
        lines.append('# 自動調査で強い外的要因/異常兆候を検出した銀河 (name,reason)')
    for nm, why in bl:
        if nm not in existing:
            lines.append(f"{nm},{why}")
    with args.blacklist.open('a', encoding='utf-8') as f:
        if lines:
            f.write("\n".join(lines) + "\n")
    print(f"wrote memos to {args.outdir}; blacklist entries: +{len(lines)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
