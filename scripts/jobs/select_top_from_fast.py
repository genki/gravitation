#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
from typing import List, Tuple


def load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:
        return {}


def metrics(d: dict) -> Tuple[float, float, float]:
    ind = d.get('indicators') or {}
    s = ind.get('S_shadow') or {}
    s_val = float('nan')
    p_perm = float('nan')
    if isinstance(s, dict):
        vals = s.get('values') or {}
        if isinstance(vals, dict):
            try:
                s_val = float(vals.get('global', float('nan')))
            except Exception:
                s_val = float('nan')
        perm = s.get('perm') or {}
        if isinstance(perm, dict):
            try:
                p_perm = float(perm.get('p_perm_one_sided_pos', float('nan')))
            except Exception:
                p_perm = float('nan')
    delta = d.get('delta') or {}
    try:
        d_shift = float(delta.get('FDB_minus_shift', float('nan')))
    except Exception:
        d_shift = float('nan')
    return s_val, p_perm, d_shift


def knobs(d: dict) -> Tuple[str, str, str]:
    meta = d.get('metadata') or {}
    env = meta.get('env_overrides') or {}
    q = str(env.get('BULLET_Q_KNEE', ''))
    p = str(env.get('BULLET_P', ''))
    xs = str(env.get('BULLET_XI_SAT', ''))
    return q, p, xs


def knobs_from_path(path: Path) -> Tuple[str, str, str]:
    stem = path.stem  # e.g., MACSJ0416_qk0.6_p0.7_xs1_fast
    parts = stem.split('_')
    q = p = xs = ''
    for part in parts:
        if part.startswith('qk'):
            q = part.replace('qk', '')
        elif part.startswith('p') and not p:
            # avoid 'progress' etc by checking pattern p<digits> or p<digits>.<digits>
            try:
                float(part[1:])
                p = part[1:]
            except Exception:
                continue
        elif part.startswith('xs'):
            xs = part.replace('xs', '')
    return q, p, xs


def main() -> int:
    ap = argparse.ArgumentParser(description='Select top configs from FAST runs to dispatch FULL')
    ap.add_argument('--holdout', required=True)
    ap.add_argument('--top', type=int, default=4)
    ap.add_argument('--loose-p', type=float, default=0.20, help='loose threshold for p_perm to consider (default 0.20)')
    ap.add_argument('--require-delta', type=float, default=-10.0, help='require ΔAICc(FDB−shift) <= this (default -10)')
    ap.add_argument('--print', dest='print_only', action='store_true', help='print selected list and exit')
    args = ap.parse_args()

    runs = sorted(Path('server/public/reports/holdout_runs').glob(f'{args.holdout}_*_fast.json'))
    rows: List[Tuple[Tuple[float,float,float], Tuple[str,str,str]]] = []
    for path in runs:
        data = load_json(path)
        m = metrics(data)
        k = knobs(data)
        if not all(k):
            k = knobs_from_path(path)
        if all(k):
            rows.append((m, k))

    def key(row):
        s_val, p_perm, d_shift = row[0]
        # order by: p_perm (finite, asc), then S (desc), then delta (more negative preferred)
        p_rank = 0 if (p_perm == p_perm) else 1
        return (p_rank, p_perm if p_perm == p_perm else math.inf, -s_val if s_val == s_val else math.inf, d_shift if d_shift == d_shift else math.inf)

    # primary filter: S>0, ΔAICc<=-10, p_perm<=loose_p
    cand = [row for row in rows if (row[0][0] == row[0][0] and row[0][0] > 0.0) and
                                   (row[0][2] == row[0][2] and row[0][2] <= args.require_delta) and
                                   (row[0][1] == row[0][1] and row[0][1] <= args.loose_p)]
    # fallback: S>0 か ΔAICc<=-10 のどちらかを満たす
    if not cand:
        cand = [row for row in rows if ((row[0][0] == row[0][0] and row[0][0] > 0.0) or
                                        (row[0][2] == row[0][2] and row[0][2] <= args.require_delta))]
    cand.sort(key=key)
    picks = cand[:max(1, args.top)]
    sel = ','.join([f"{k[0]}:{k[1]}:{k[2]}" for _, k in picks])
    if args.print_only:
        print(sel)
        return 0
    # write selection file for batch scripts to consume
    out = Path('tmp')/ 'jobs' / f'{args.holdout}_fast_top.txt'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(sel, encoding='utf-8')
    print(sel)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
