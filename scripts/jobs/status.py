#!/usr/bin/env python3
from __future__ import annotations
import json
import os
from pathlib import Path
from datetime import datetime

REPO_ROOT = Path(__file__).resolve().parents[2]
JOBS_DIR = REPO_ROOT / "tmp" / "jobs"

if not JOBS_DIR.exists():
    print("No jobs directory (tmp/jobs).")
    raise SystemExit(0)

meta_files = sorted(JOBS_DIR.glob('*.json'))
if not meta_files:
    print("No job metadata found in tmp/jobs.")
    raise SystemExit(0)

for meta in meta_files:
    try:
        data = json.loads(meta.read_text())
    except Exception as exc:
        print(f"{meta.name}: unable to read JSON ({exc})")
        continue
    pid = data.get('pid')
    started = data.get('started')
    holdout = data.get('holdout')
    train = data.get('train')
    log_file = data.get('log_file')
    progress_log = data.get('progress_log')
    command = data.get('command')
    running = False
    if isinstance(pid, int) and pid > 0:
        try:
            os.kill(pid, 0)
        except OSError:
            running = False
        else:
            running = True
    status = 'running' if running else 'stopped'
    print(f"{meta.stem} -> {status}")
    print(f"  PID       : {pid}")
    print(f"  Holdout   : {holdout}")
    print(f"  Train     : {train}")
    if started:
        print(f"  Started   : {started}")
    if log_file:
        print(f"  Log file  : {log_file}")
    if progress_log:
        print(f"  Progress  : {progress_log}")
    if command:
        print(f"  Command   : {command}")
    if not running:
        print("  Note      : process not running; remove metadata when finished inspecting logs.")
    print()
