#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from datetime import datetime, timezone


def main():
    ap = argparse.ArgumentParser(description='Append a question to the research policy lead list')
    ap.add_argument('question', help='Question text')
    ap.add_argument('--who', default='', help='Asker name/initials')
    ap.add_argument('--file', default='data/questions_to_lead.json', help='JSON file path')
    args = ap.parse_args()
    p = Path(args.file)
    data = {"updated": "", "items": []}
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            pass
    if 'items' not in data or not isinstance(data['items'], list):
        data['items'] = []
    now = datetime.now(timezone.utc).isoformat()
    data['items'].append({"q": args.question, "who": args.who or None, "ts": now})
    data['updated'] = now
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"Appended question. Total: {len(data['items'])}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

