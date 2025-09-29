#!/usr/bin/env python3
from __future__ import annotations
import re, sys, hashlib
from pathlib import Path

"""
Check that server/public/state_of_the_art/index.html displays the SHA fingerprint
of data/shared_params.json that matches the actual file.
Exits 0 on success; 1 on failure (to fail CI).
"""

def main() -> int:
    idx = Path('server/public/state_of_the_art/index.html')
    sp = Path('data/shared_params.json')
    if not idx.exists() or not sp.exists():
        print('missing index.html or shared_params.json', file=sys.stderr)
        return 1
    html = idx.read_text(encoding='utf-8', errors='ignore')
    m = re.search(r'sha256:([0-9a-fA-F]{12})', html)
    if not m:
        print('sha fingerprint not found in SOTA index', file=sys.stderr)
        return 1
    shown = m.group(1).lower()
    real = hashlib.sha256(sp.read_bytes()).hexdigest()[:12]
    if shown != real:
        print(f'sha mismatch: shown={shown} real={real}', file=sys.stderr)
        return 1
    print('shared_params sha OK:', real)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

