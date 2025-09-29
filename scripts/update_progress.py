#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
import argparse


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rate", type=float, required=True, help="現在の進捗率(0..100)")
    ap.add_argument("--note", type=str, default="", help="任意のメモ")
    ap.add_argument("--file", type=Path, default=Path("data/progress.json"))
    args = ap.parse_args()

    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST).strftime("%Y-%m-%d %H:%M:%S %Z")
    rec = {"ts": now, "rate": float(args.rate), "note": args.note}

    data = {"history": []}
    if args.file.exists():
        try:
            data = json.loads(args.file.read_text(encoding="utf-8"))
            if not isinstance(data.get("history"), list):
                data = {"history": []}
        except Exception:
            data = {"history": []}
    data["history"].append(rec)
    args.file.parent.mkdir(parents=True, exist_ok=True)
    args.file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("saved:", args.file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

