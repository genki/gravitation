#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
import numpy as np
from fdb.mu0 import mu0_of_k


def main() -> int:
    ap = argparse.ArgumentParser(description='Verify μ0(k→∞)→1 and report deviations')
    ap.add_argument('--eps', type=float, default=1.0)
    ap.add_argument('--k0', type=float, default=0.2)
    ap.add_argument('--m', type=float, default=2.0)
    args = ap.parse_args()
    ks = np.geomspace(1e-3*args.k0, 1e4*args.k0, 2000)
    mu = mu0_of_k(ks, args.eps, args.k0, args.m)
    dev_hi = float(abs(mu[-1] - 1.0))
    dev_lo = float(abs(mu[0] - (1.0 + args.eps/(1.0 + (ks[0]/args.k0)**args.m))))
    out = {
        'eps': args.eps, 'k0': args.k0, 'm': args.m,
        'k_hi': float(ks[-1]), 'mu_hi': float(mu[-1]), 'dev_hi': dev_hi,
        'k_lo': float(ks[0]), 'mu_lo': float(mu[0]), 'dev_lo': dev_lo,
        'ok_hi': (dev_hi <= 1e-6)
    }
    print(json.dumps(out, indent=2))
    return 0 if out['ok_hi'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

