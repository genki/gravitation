#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any


REPO = Path(__file__).resolve().parents[2]
JOBS = REPO / 'tmp' / 'jobs'
DST = REPO / 'server/public/state_of_the_art/jobs.html'


def load_jobs() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if not JOBS.exists():
        return items
    for p in sorted(JOBS.glob('*.json')):
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
            data['_path'] = str(p)
            items.append(data)
        except Exception:
            continue
    return items


def html_escape(s: str) -> str:
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def main() -> int:
    jobs = load_jobs()
    rows: List[str] = []
    for j in jobs:
        name = html_escape(str(j.get('name') or Path(j.get('_path', '')).stem))
        pid = str(j.get('pid') or j.get('pgid') or '')
        started = html_escape(str(j.get('started') or ''))
        log = html_escape(str(j.get('log_file') or ''))
        workdir = html_escape(str(j.get('workdir') or ''))
        cmd = html_escape(str(j.get('command') or ''))
        log_link = log
        if log.startswith(str(REPO)):
            rel = str(Path(log).relative_to(REPO))
            log_link = f'../{rel}'
        rows.append(
            f'<tr><td>{name}</td><td>{pid}</td><td>{started}</td><td><a href="{log_link}">{log_link}</a></td><td><code>{cmd}</code></td></tr>'
        )
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>BGジョブ一覧</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        '<main class="wrap"><h1>バックグラウンドジョブ一覧</h1>',
        '<div class=card><table class="t"><thead><tr><th>Name</th><th>PID/PGID</th><th>Started</th><th>Log</th><th>Command</th></tr></thead><tbody>',
        '\n'.join(rows) if rows else '<tr><td colspan=5><small>ジョブはありません。</small></td></tr>',
        '</tbody></table></div>',
        '</main></body></html>'
    ]
    DST.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', DST)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

