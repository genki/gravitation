#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess as sp
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description='Refit with shared μ0(k) fixed; per-galaxy fit Υ★ (and global aniso_lambda)')
    ap.add_argument('--names-file', type=Path, required=True)
    ap.add_argument('--eps', type=float, default=1.0)
    ap.add_argument('--k0', type=float, default=0.2)
    ap.add_argument('--m', type=int, default=2)
    ap.add_argument('--gas', type=float, default=1.33)
    ap.add_argument('--aniso-lambda', type=float, default=0.0)
    ap.add_argument('--out', type=Path, default=Path('data/results/refit_fixed_hyper.json'))
    args = ap.parse_args()
    cmd = [
        'PYTHONPATH=.', './.venv/bin/python', 'scripts/compare_fit_multi.py',
        '--names-file', str(args.names_file),
        '--boost', '0.5', '--boost-tie-lam', '--auto-geo',
        '--pad-factor', '2', '--eg-frac-floor', '0.15', '--err-floor-kms', '5',
        '--inv1-orth', '--line-eps', '0.8',
        '--mu-eps-grid', f'{args.eps}', '--mu-k0-grid', f'{args.k0}', '--mu-m-grid', f'{args.m}',
        '--gas-scale-grid', f'{args.gas}', '--aniso-lambda', f'{args.aniso_lambda}', '--out', str(args.out)
    ]
    sp.run(' '.join(cmd), shell=True, check=True)
    print('saved', args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

