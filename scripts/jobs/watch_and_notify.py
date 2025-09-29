#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess as sp
import sys
import time
from pathlib import Path
from typing import Dict, Any


REPO = Path(__file__).resolve().parents[2]
JOBS_DIR = REPO / 'tmp' / 'jobs'
STATE = JOBS_DIR / '_watch_state.json'
ENV_DOTFILE = REPO / '.env'


def load_env_from_dotfile() -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not ENV_DOTFILE.exists():
        return env
    try:
        for line in ENV_DOTFILE.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip()
    except Exception:
        pass
    return env


def pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def load_state() -> Dict[str, Any]:
    if not STATE.exists():
        return {'notified': []}
    try:
        return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception:
        return {'notified': []}


def save_state(st: Dict[str, Any]) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(st, indent=2), encoding='utf-8')
    except Exception:
        pass


def notify(title: str, message: str) -> None:
    env = os.environ.copy()
    env.update(load_env_from_dotfile())
    cmd = [str(REPO / 'scripts' / 'notice.sh'), '-m', message, '-t', title]
    try:
        sp.run(cmd, cwd=str(REPO), check=False, env=env, stdout=sp.PIPE, stderr=sp.STDOUT, text=True)
    except Exception:
        pass


def rebuild_links() -> None:
    try:
        sp.run([sys.executable, str(REPO / 'scripts' / 'reports' / 'make_jobs_dashboard.py')],
               cwd=str(REPO), check=False)
        sp.run([sys.executable, str(REPO / 'scripts' / 'build_state_of_the_art.py')],
               cwd=str(REPO), check=False)
    except Exception:
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description='Watch tmp/jobs/*.json and send a notice when jobs finish')
    ap.add_argument('--interval', type=float, default=20.0)
    args = ap.parse_args()
    st = load_state()
    notified = set(st.get('notified', []))
    while True:
        # scan job metadata
        jobs = sorted(JOBS_DIR.glob('*.json')) if JOBS_DIR.exists() else []
        changed = False
        for meta in jobs:
            if meta.name.startswith('_'):
                continue
            if meta.name in notified:
                continue
            try:
                data = json.loads(meta.read_text(encoding='utf-8'))
            except Exception:
                continue
            pid = int(data.get('pid') or 0)
            name = str(data.get('name') or meta.stem)
            log = str(data.get('log_file') or '')
            # consider finished if PID not running
            if not pid_running(pid):
                title = f'BGジョブ完了: {name}'
                msg_lines = [
                    f'- PID: {pid}',
                    f'- Log: {log}' if log else '- Log: (none)',
                    '- 進捗: SOTAのJobs/HO進捗からも確認可能',
                ]
                notify(title, '\n'.join(msg_lines))
                notified.add(meta.name)
                changed = True
        if changed:
            st['notified'] = sorted(notified)
            save_state(st)
            rebuild_links()
        time.sleep(max(2.0, float(args.interval)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

