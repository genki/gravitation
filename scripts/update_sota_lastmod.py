#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re


def main():
    p = Path("docs/state-of-the-art.md")
    if not p.exists():
        return
    txt = p.read_text(encoding="utf-8")
    # Local time with minutes and numeric TZ (YYYY-MM-DD HH:MM ±TZ)
    now = datetime.now(timezone.utc).astimezone()
    tzmin = -now.utcoffset().total_seconds() // 60 if now.utcoffset() else 0
    sign = '+' if tzmin <= 0 else '-'
    tzabs = int(abs(tzmin))
    tzstr = f"{sign}{tzabs//60:02d}{tzabs%60:02d}"
    today = now.strftime('%Y-%m-%d %H:%M ') + tzstr
    lines = txt.splitlines()
    # 見出しの直後にLast updated行を強制配置
    for i, ln in enumerate(lines):
        if ln.startswith("# State of the Art"):
            header_idx = i
            break
    else:
        header_idx = 0
    # 再構成: 見出し直下に最新の1行を挿入し、それ以外の"Last updated:"は全削除
    new_lines = []
    for i, ln in enumerate(lines):
        if i == header_idx:
            new_lines.append(ln)
            new_lines.append(f"Last updated: {today}")
            continue
        if ln.strip().startswith("Last updated:") or ln.strip().startswith("最終更新:"):
            continue
        new_lines.append(ln)
    txt2 = "\n".join(new_lines)
    # 余計な単独日付行（例: "P25-08-31"）を除去（先頭10行のみ）
    txt3 = txt2
    if txt3 != txt:
        p.write_text(txt3, encoding="utf-8")
        print("Updated lastmod to", today)
    else:
        print("No change")


if __name__ == "__main__":
    main()
