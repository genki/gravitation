#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess as sp
from pathlib import Path


def run_once(names: Path, eps: float, k0: float, m: int, gas: float, out: Path) -> dict:
    args = [
        'PYTHONPATH=.', './.venv/bin/python', 'scripts/compare_fit_multi.py',
        '--names-file', str(names), '--boost', '0.5', '--boost-tie-lam', '--auto-geo',
        '--pad-factor', '2', '--eg-frac-floor', '0.15', '--err-floor-kms', '5', '--inv1-orth', '--line-eps', '0.8',
        '--mu-eps-grid', f'{eps}', '--mu-k0-grid', f'{k0}', '--mu-m-grid', f'{m}', '--gas-scale-grid', f'{gas}',
        '--aniso-lambda', '0.0', '--out', str(out)
    ]
    sp.run(' '.join(args), shell=True, check=True)
    return json.loads(out.read_text(encoding='utf-8'))


def main() -> int:
    ap = argparse.ArgumentParser(description='One-shot micro tuning of (eps,k0) by grid ±30% around baseline, pick best by AICc')
    ap.add_argument('--names-file', type=Path, required=True)
    ap.add_argument('--eps', type=float, default=1.0)
    ap.add_argument('--k0', type=float, default=0.2)
    ap.add_argument('--m', type=int, default=2)
    ap.add_argument('--gas', type=float, default=1.33)
    ap.add_argument('--steps', type=int, default=3, help='per-axis steps (>=2)')
    ap.add_argument('--out-dir', type=Path, default=Path('data/results/micro_tune'))
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    best = (float('inf'), None, None)
    factors = [1.0 - 0.3, 1.0, 1.0 + 0.3] if args.steps <= 3 else [1.0 - 0.3, 1.0 - 0.15, 1.0, 1.0 + 0.15, 1.0 + 0.3]
    tried = []
    for fe in factors:
        for fk in factors:
            e = max(1e-6, args.eps * fe)
            k = max(1e-6, args.k0 * fk)
            out = args.out_dir / f'fit_eps{e:.3f}_k0_{k:.3f}.json'
            res = run_once(args.names_file, e, k, args.m, args.gas, out)
            AIC = res.get('AIC', {})
            k_gr = (AIC.get('k') or {}).get('GR'); k_ulw = (AIC.get('k') or {}).get('ULW')
            Ntot = res.get('N_total', {})
            N_gr = Ntot.get('GR'); N_ulw = Ntot.get('ULW')
            def aicc(AICv, kv, Nv):
                try:
                    A, K, N = float(AICv or 0.0), int(kv or 0), int(Nv or 0)
                    return A + (2*K*(K+1))/(N-K-1) if (N-K-1)>0 else float('inf')
                except Exception:
                    return float('inf')
            aicc_ulw = aicc(AIC.get('ULW'), k_ulw, N_ulw)
            tried.append({'eps': e, 'k0': k, 'AICc_ULW': aicc_ulw})
            if aicc_ulw < best[0]:
                best = (aicc_ulw, e, k)
    outj = args.out_dir / 'micro_tune_result.json'
    outj.write_text(json.dumps({'baseline': {'eps': args.eps, 'k0': args.k0}, 'best': {'eps': best[1], 'k0': best[2], 'AICc_ULW': best[0]}, 'tried': tried}, indent=2), encoding='utf-8')
    print(json.dumps({'best': {'eps': best[1], 'k0': best[2], 'AICc_ULW': best[0]}}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

