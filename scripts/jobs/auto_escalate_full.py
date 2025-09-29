#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess as sp
import sys
import time
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
CLUSTER_DIR = REPO_ROOT / "server/public/reports/cluster"
LOG_DIR = REPO_ROOT / "server/public/reports/logs"


def read_p_value(holdout: str) -> Optional[float]:
    p = CLUSTER_DIR / f"{holdout}_holdout.json"
    if not p.exists():
        return None
    try:
        j = json.loads(p.read_text(encoding="utf-8"))
        s = (j.get("indicators") or {}).get("S_shadow") or {}
        perm = (s.get("perm") or {})
        v = perm.get("p_perm_one_sided_pos")
        return float(v) if v is not None else None
    except Exception:
        return None


def run_full(holdout: str) -> int:
    """Launch FULL holdout via BG dispatcher so job watcher can notify Slack."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    job_name = f"auto_full_{holdout}"
    # Command to run under dispatcher
    inner = (
        "set -e; "
        # Constrain BLAS threads and glibc arena growth to reduce RAM spikes
        "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2 "
        "PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py "
        f"--train Abell1689,CL0024 --holdout {holdout} "
        "--sigma-psf 1.0,1.5,2.0 --sigma-highpass 1.0,1.5 "
        "--roi-quantiles 0.70,0.80,0.85 --band 4-8,8-16 "
        "--perm-n 10000; "
        "echo '[auto-escalate] FULL finished'"
    )
    dispatch = [
        str(REPO_ROOT / 'scripts' / 'jobs' / 'dispatch_bg.sh'),
        '-n', job_name, '--', inner
    ]
    proc = sp.Popen(dispatch, cwd=str(REPO_ROOT))
    return proc.pid


def main() -> int:
    ap = argparse.ArgumentParser(description="Monitor FAST holdouts and escalate to FULL when p<success-p")
    ap.add_argument("--holdouts", default="MACSJ0416,AbellS1063", help="Comma-separated holdout names")
    ap.add_argument("--interval", type=float, default=30.0, help="Polling interval [s]")
    ap.add_argument("--timeout", type=float, default=1800.0, help="Timeout [s]")
    ap.add_argument("--success-p", type=float, default=0.02, help="p threshold for escalation")
    args = ap.parse_args()

    names = [s.strip() for s in (args.holdouts or "").split(",") if s.strip()]
    if not names:
        print("[auto-escalate] no holdouts specified", file=sys.stderr)
        return 2
    t0 = time.time()
    todo = set(names)
    escalated: dict[str, int] = {}
    while todo and (time.time() - t0) < args.timeout:
        for h in list(todo):
            p = read_p_value(h)
            if p is None:
                continue
            if p < args.success_p:
                pid = run_full(h)
                escalated[h] = pid
                todo.remove(h)
                print(f"[auto-escalate] Escalated {h} to FULL (pid={pid})")
        time.sleep(args.interval)
    if todo:
        print(f"[auto-escalate] timeout; not escalated: {sorted(todo)}")
    else:
        print(f"[auto-escalate] done; escalated: {escalated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
