#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess as sp
from pathlib import Path
from typing import List, Tuple

REPO = Path(__file__).resolve().parents[2]


def parse_name(p: Path) -> Tuple[str, str, float, float]:
    name = p.stem
    parts = name.split('_')
    se = ''
    psf = float('nan')
    hp = float('nan')
    for token in parts:
        if token.startswith('se-'):
            se = token[3:]
        elif token.startswith('psf-'):
            try:
                psf = float(token[4:])
            except Exception:
                psf = float('nan')
        elif token.startswith('hp-'):
            try:
                hp = float(token[3:])
            except Exception:
                hp = float('nan')
    return name, se, psf, hp


def rank_candidates(dirpath: Path) -> List[dict]:
    rows: List[dict] = []
    for p in sorted(dirpath.glob('*.json')):
        try:
            j = json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            continue
        _, se, psf, hp = parse_name(p)
        s = j.get('S_shadow') or j.get('indicators', {}).get('S_shadow') or {}
        perm = s.get('perm') or {}
        sval = (s.get('values') or {}).get('global')
        p_perm = perm.get('p_perm_one_sided_pos')
        delta = j.get('delta') or {}
        d_shift = delta.get('FDB_minus_shift')
        rows.append({
            'path': str(p),
            'se': se,
            'psf': psf,
            'hp': hp,
            'S_shadow': float(sval) if isinstance(sval, (int, float)) else float('nan'),
            'p_perm': float(p_perm) if isinstance(p_perm, (int, float)) else float('nan'),
            'delta_shift': float(d_shift) if isinstance(d_shift, (int, float)) else float('nan'),
        })
    # sort: prefer smaller p_perm, then larger S_shadow, then more negative ΔAICc(FDB−shift)
    rows.sort(key=lambda r: (
        r['p_perm'] if r['p_perm'] == r['p_perm'] else 1.0,
        -(r['S_shadow'] if r['S_shadow'] == r['S_shadow'] else -1e9),
        r['delta_shift'] if r['delta_shift'] == r['delta_shift'] else 1e9,
    ))
    return rows


def dispatch_full(holdout: str, se: str, psf: float, hp: float, train: str) -> int:
    job = f"a4_full_{holdout}_se-{se}_psf-{psf}_hp-{hp}"
    env = (
        "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "
        "NUMEXPR_MAX_THREADS=1 MALLOC_ARENA_MAX=2 PYTHONMALLOC=malloc"
    )
    inner = (
        "set -e; "
        f"{env} BULLET_SE_TRANSFORM={shlex.quote(se)} PYTHONPATH=. ./.venv/bin/python scripts/reports/make_bullet_holdout.py "
        f"--train {shlex.quote(train)} --holdout {shlex.quote(holdout)} --sigma-psf {psf} --sigma-highpass {hp} "
        "--band 8-16 --perm-n 5000 --perm-min 5000 --perm-max 5000; "
        "echo '[a4-full] finished'"
    )
    cmd = [str(REPO / 'scripts' / 'jobs' / 'dispatch_bg.sh'), '-n', job, '--', inner]
    sp.Popen(cmd, cwd=str(REPO))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description='Select top A-4 FAST configs and dispatch FULL runs')
    ap.add_argument('--holdout', required=True)
    ap.add_argument('--train', default='Abell1689,CL0024')
    ap.add_argument('--top', type=int, default=1)
    ap.add_argument('--dir', default=None, help='snapshot dir; default server/public/reports/a4_fast/<holdout>')
    args = ap.parse_args()
    d = Path(args.dir) if args.dir else (REPO / 'server/public/reports/a4_fast' / args.holdout)
    if not d.exists():
        print(f"[a4-full] snapshot dir not found: {d}")
        return 0
    rows = rank_candidates(d)
    if not rows:
        print('[a4-full] no snapshots yet; nothing to dispatch')
        return 0
    for r in rows[: max(1, int(args.top))]:
        dispatch_full(args.holdout, r['se'], r['psf'], r['hp'], args.train)
        print(f"[a4-full] dispatched FULL: se={r['se']} psf={r['psf']} hp={r['hp']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

