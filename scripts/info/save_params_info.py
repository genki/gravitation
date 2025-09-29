#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, time
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description='Save info-decoherence model params for reproducibility')
    ap.add_argument('--out', type=Path, default=Path('data/params_info.json'))
    ap.add_argument('--kappa', type=float, default=1.0, help='overall scale κ')
    ap.add_argument('--beta', type=float, default=0.3, help='forwardization phase kernel β (0..1)')
    ap.add_argument('--eta-model', default='small_k_quadratic', help='eta model id')
    ap.add_argument('--D', type=float, default=0.0, help='diffusion coefficient (UWM-D) [kpc^2/Myr]')
    ap.add_argument('--tau', type=float, default=1.0, help='damping timescale τ [Myr]')
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'kappa': float(args.kappa),
        'beta': float(args.beta),
        'eta_model': str(args.eta_model),
        'D': float(args.D),
        'tau': float(args.tau),
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'notes': 'UWM(=ULM) info-flow params; saved by save_params_info.py',
    }
    args.out.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print('wrote', args.out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

