#!/usr/bin/env python3
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path


def inject_lastmod(html: str, epoch_ms: int) -> str:
    lines = html.splitlines()
    out = []
    inserted_meta = False
    inserted_script = False
    for ln in lines:
        if (not inserted_meta) and ('<head>' in ln):
            out.append(ln)
            out.append(f'  <meta name="x-last-updated-epoch" content="{epoch_ms}">')
            inserted_meta = True
            continue
        out.append(ln)
    # also add a small inline script before closing head if not present
    if '</head>' in html:
        tmp = []
        for ln in out:
            if (not inserted_script) and ('</head>' in ln):
                tmp.append(f'  <script>window.SOTA_LAST_UPDATED={epoch_ms}; document.dispatchEvent(new Event("sota:lastmod"));</script>')
                tmp.append(ln)
                inserted_script = True
            else:
                tmp.append(ln)
        out = tmp
    return "\n".join(out)


def main() -> int:
    idx = Path('server/public/index.html')
    if not idx.exists():
        return 0
    html = idx.read_text(encoding='utf-8')
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    html2 = inject_lastmod(html, now_ms)
    if html2 != html:
        idx.write_text(html2, encoding='utf-8')
        print('Updated root index lastmod to', now_ms)
    else:
        print('No change (root index)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

