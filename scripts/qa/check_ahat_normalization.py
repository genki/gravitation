#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
import numpy as np


def ahat_mean_error(a2: float, n: tuple[float,float,float], nsamp: int = 200000) -> float:
    n = np.asarray(n, dtype=float)
    n = n / (np.linalg.norm(n) + 1e-30)
    # random directions on sphere via normal sampling
    v = np.random.normal(size=(nsamp,3))
    v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-30)
    cos2 = (v @ n)**2
    ahat = 1.0 + a2 * (cos2 - 1.0/3.0)
    return float(abs(ahat.mean() - 1.0))


def main() -> int:
    ap = argparse.ArgumentParser(description='Check ⟨Â_y⟩_Ω = 1 numerically for l=2 form')
    ap.add_argument('--a2', type=float, default=0.5)
    ap.add_argument('--nsamp', type=int, default=200000)
    args = ap.parse_args()
    err = ahat_mean_error(args.a2, (0,0,1), nsamp=args.nsamp)
    out = {'a2': args.a2, 'nsamp': args.nsamp, 'mean_error': err, 'ok': (err <= 1e-3)}
    print(json.dumps(out, indent=2))
    return 0 if out['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

