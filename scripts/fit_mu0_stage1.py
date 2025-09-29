#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
import numpy as np


def mu0_model(k: np.ndarray, eps: float, k0: float, m: float) -> np.ndarray:
    return 1.0 + eps / (1.0 + (k / k0) ** m)


def fit_mu0_grid(k: np.ndarray, mu_obs: np.ndarray, w: np.ndarray | None = None,
                 eps_grid=None, k0_grid=None, m_grid=None):
    if w is None:
        w = np.ones_like(k)
    if eps_grid is None:
        eps_grid = np.linspace(0.0, 2.0, 41)
    if k0_grid is None:
        kmin = np.percentile(k[k>0], 10)
        kmax = np.percentile(k, 90)
        k0_grid = np.geomspace(max(kmin*0.25, 1e-6), max(kmax, 1e-5), 41)
    if m_grid is None:
        m_grid = np.linspace(1.5, 8.0, 27)
    best = (np.inf, None)
    for eps in eps_grid:
        for k0 in k0_grid:
            for m in m_grid:
                mu_hat = mu0_model(k, eps, k0, m)
                err = np.average((mu_hat - mu_obs)**2, weights=w)
                if err < best[0]:
                    best = (err, (float(eps), float(k0), float(m)))
    return best[1], best[0]


def main():
    ap = argparse.ArgumentParser(description='Stage-1 fit for μ0(k)=1+ε/(1+(k/k0)^m)')
    ap.add_argument('csv', help='Input CSV with columns: k, mu_obs[, w]')
    ap.add_argument('--out', default='mu0_stage1.json', help='Output JSON path')
    args = ap.parse_args()
    data = np.genfromtxt(args.csv, delimiter=',', names=True)
    k = np.asarray(data['k'], dtype=float)
    mu_obs = np.asarray(data['mu_obs'], dtype=float)
    w = np.asarray(data['w'], dtype=float) if 'w' in data.dtype.names else None
    (eps, k0, m), loss = fit_mu0_grid(k, mu_obs, w)
    out = {
        'epsilon': eps,
        'k0': k0,
        'm': m,
        'loss_mse': float(loss),
        'notes': 'Grid search; refine with robust loss as needed.'
    }
    with open(args.out, 'w') as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

