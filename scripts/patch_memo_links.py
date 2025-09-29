#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path


def patch_file(p: Path) -> bool:
    s = p.read_text(encoding='utf-8')
    lines = s.splitlines()
    out = []
    in_links = False
    changed = False
    # Capture 参考リンク block to move to bottom
    links_block: list[str] | None = None
    i = 0
    while i < len(lines):
        ln = lines[i]
        # Capture '参考リンク' section as a block to move later (handle before generic header)
        if ln.strip() == '## 参考リンク':
            # collect until next header or EOF
            j = i
            blk = []
            while j < len(lines):
                blk_ln = lines[j]
                if j != i and blk_ln.strip().startswith('## '):
                    break
                blk.append(blk_ln)
                j += 1
            # store and skip
            links_block = blk
            changed = True
            i = j
            continue
        if ln.strip().startswith('## '):
            in_links = (ln.strip() == '## 参考リンク')
            out.append(ln)
            i += 1
            continue
        if in_links:
            # stop at next header
            if ln.strip().startswith('## '):
                in_links = False
                out.append(ln)
                i += 1
                continue
            m = re.match(r"^\-\s+([^:\]]+):\s+(https?://\S+)\s*$", ln)
            if m:
                label, url = m.group(1).strip(), m.group(2).strip()
                out.append(f"- [{label}]({url})")
                changed = True
                i += 1
                continue
            m2 = re.match(r"^\-\s+(https?://\S+)\s*$", ln)
            if m2:
                url = m2.group(1).strip()
                out.append(f"- [{url}]({url})")
                changed = True
                i += 1
                continue
        out.append(ln)
        i += 1
    # Append 参考リンク block at bottom if captured
    if links_block:
        # Ensure single trailing blank line
        if out and out[-1].strip() != '':
            out.append('')
        out.extend(links_block)
    if changed or links_block:
        p.write_text("\n".join(out) + "\n", encoding='utf-8')
    return bool(changed or links_block)


def main() -> int:
    root = Path('memo/galaxies')
    if not root.exists():
        return 0
    cnt = 0
    for p in root.glob('*.md'):
        if patch_file(p):
            cnt += 1
    print(f'patched {cnt} files')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
