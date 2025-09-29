#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set
import time


def h(s: str) -> str:
    return (
        str(s)
        .replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def load_index(p: Path) -> Dict[str, Any]:
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def load_blacklist(p: Path) -> Dict[str, str]:
    res: Dict[str, str] = {}
    if not p.exists():
        return res
    for ln in p.read_text(encoding='utf-8').splitlines():
        s = ln.strip()
        if not s or s.startswith('#'):
            continue
        parts = s.split(',', 1)
        if len(parts) == 2:
            res[parts[0].strip()] = parts[1].strip()
        else:
            res[parts[0].strip()] = ''
    return res


def load_exclude_env(p: Path) -> Set[str]:
    if not p.exists():
        return set()
    out: Set[str] = set()
    for ln in p.read_text(encoding='utf-8').splitlines():
        s = ln.strip()
        if s and not s.startswith('#'):
            out.add(s)
    return out


def write_html(out: Path, title: str, body: str) -> None:
    last_epoch_ms = int(time.time() * 1000)
    # depth-aware relative prefix from server/public
    try:
        rel = out.resolve().relative_to(Path('server/public').resolve())
        depth = max(len(rel.parts) - 1, 0)
    except Exception:
        depth = 0
    pref = '../' * depth
    html = (
        "<!doctype html>\n"
        "<html lang=\"ja-JP\">\n<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"  <title>{h(title)}</title>\n"
        f"  <link rel=\"stylesheet\" href=\"{pref}styles.css\">\n"
        "  <style>.badge{padding:2px 6px;border-radius:4px;background:#eee}"
        ".y{background:#ffe08a}.r{background:#ffb3a7}.g{background:#c8f7c5}"
        ".tbl{width:100%;border-collapse:collapse} .tbl th,.tbl td{padding:6px 8px;border-bottom:1px solid #eee}"
        ".nowrap{white-space:nowrap} .muted{color:#666;font-size:90%}</style>\n"
        "  <script>function f(){var q=document.getElementById('q').value.toLowerCase();"
        "var rows=document.querySelectorAll('tbody tr');rows.forEach(function(r){"
        "var s=r.getAttribute('data-k');r.style.display=s.indexOf(q)>=0?'':'none';});}</script>\n"
        "</head>\n<body>\n"
        "  <header class=\"site-header\">\n"
        "    <div class=\"wrap\">\n"
        "      <div class=\"brand\">研究進捗</div>\n"
        "      <nav class=\"nav\">\n"
        f"        <a href=\"{pref}index.html\">ホーム</a>\n"
        f"        <a href=\"{pref}state_of_the_art/index.html\">State of the Art</a>\n"
        f"        <a href=\"{pref}reports/index.html\">レポート</a>\n"
        "      </nav>\n"
        "    </div>\n"
        "  </header>\n"
        "  <main class=\"wrap\">\n" + body + "\n  </main>\n"
        "  <footer class=\"site-footer\">\n"
        "    <div class=\"wrap\">ローカル配信(開発用)</div>\n"
        "  </footer>\n"
        "</body>\n</html>\n"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')


def main() -> int:
    idx = load_index(Path('memo/galaxies/index.json'))
    bl = load_blacklist(Path('data/sparc/sets/blacklist.txt'))
    ex = load_exclude_env(Path('data/sparc/sets/exclude_env.txt'))
    names = sorted(idx.keys())

    # Header
    body: List[str] = []
    body.append('<h1>銀河プロファイル一覧</h1>')
    body.append('<p class="muted">Wikipedia要約から自動生成した調査メモと、外的要因の兆候（暫定）を一覧表示します。詳細は各メモを参照し、人手確認のうえ <code>exclude_env.txt</code> に反映してください。</p>')
    body.append('<input id="q" oninput="f()" placeholder="フィルタ: galaxy / flag / status" style="width:100%;padding:8px;margin:8px 0">')
    # Table
    body.append('<table class="tbl"><thead><tr>'
                '<th>Galaxy</th><th>Flags</th><th>Status</th><th class="nowrap">Memo</th>'
                '</tr></thead><tbody>')
    for nm in names:
        v = idx.get(nm, {})
        flags: List[str] = v.get('flags') or []
        flag_txt = ', '.join(flags) if flags else '-'
        status = []
        if nm in bl:
            status.append(f"<span class=\"badge r\">blacklist</span>")
        if nm in ex:
            status.append(f"<span class=\"badge y\">excluded(manual)</span>")
        if not status:
            status.append(f"<span class=\"badge g\">ok</span>")
        memo_link = f"../memo/galaxies/{h(nm)}.md"
        keys = (nm + ' ' + flag_txt + ' ' + ('blacklist' if nm in bl else '') + (' excluded' if nm in ex else '')).lower()
        body.append(
            f"<tr data-k=\"{h(keys)}\"><td class=nowrap>{h(nm)}</td>"
            f"<td>{h(flag_txt)}</td><td>{''.join(status)}</td>"
            f"<td><a href=\"{memo_link}\">memo</a></td></tr>"
        )
    body.append('</tbody></table>')
    write_html(Path('server/public/galaxies/index.html'), 'Galaxy Profiles', '\n'.join(body))
    print('wrote: server/public/galaxies/index.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
