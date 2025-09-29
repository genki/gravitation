#!/usr/bin/env python3
"""Monitor fdb_volume log files and stream incremental updates.

Intended for long-running Monte Carlo validation jobs so that background
processes still expose progress every few seconds.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict

DEFAULT_DIR = Path("logs/fdb_volume")
DEFAULT_EXTS = (".log", ".out")


def discover_logs(log_dir: Path, extensions: tuple[str, ...]) -> list[Path]:
    if not log_dir.exists():
        return []
    files = []
    for path in sorted(log_dir.glob("**/*")):
        if path.is_file() and path.suffix in extensions:
            files.append(path)
    return files


def stream_updates(log_dir: Path, interval: float, extensions: tuple[str, ...]) -> None:
    positions: Dict[Path, int] = {}
    try:
        while True:
            files = discover_logs(log_dir, extensions)
            if not files:
                print(f"[watch] no log files under {log_dir} yet", file=sys.stderr)
            for path in files:
                last = positions.get(path, 0)
                size = path.stat().st_size
                if size < last:
                    last = 0  # file truncated; restart from beginning
                if size == last:
                    positions[path] = size
                    continue
                with path.open("r", encoding="utf-8", errors="replace") as fp:
                    fp.seek(last)
                    chunk = fp.read()
                if chunk:
                    for line in chunk.splitlines():
                        print(f"[{path.name}] {line}")
                positions[path] = size
            sys.stdout.flush()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[watch] stopped", file=sys.stderr)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stream updates from fdb_volume logs")
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=DEFAULT_DIR,
        help="Directory containing log files (default: logs/fdb_volume)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--ext",
        nargs="*",
        default=list(DEFAULT_EXTS),
        help="File extensions to include (default: .log .out)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    log_dir: Path = args.log_dir
    interval: float = max(args.interval, 1.0)
    extensions = tuple(e if e.startswith(".") else f".{e}" for e in args.ext)
    log_dir.mkdir(parents=True, exist_ok=True)
    stream_updates(log_dir, interval, extensions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
