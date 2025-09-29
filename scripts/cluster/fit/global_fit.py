#!/usr/bin/env python3
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
import subprocess


def aicc(chi2: float, k: int, N: int) -> float:
    if N - k - 1 <= 0:
        return float('nan')
    return float(chi2 + 2 * k + (2 * k * (k + 1)) / (N - k - 1))


def fit_one(kappa_obs: np.ndarray, W: np.ndarray, S: np.ndarray, alpha: float, beta: float, C: float) -> float:
    # recompute W,S for given alpha,beta by simple scaling proxies
    Wt = np.exp(-alpha) ** (W * 0 + 1) * W / np.exp(-0.0)  # keep shape; placeholder sensitivity
    St = (1.0 + 0.2 * beta) * S
    src = Wt * St
    # fast 1/r via FFT
    ny, nx = src.shape
    y = (np.arange(ny) - (ny - 1) / 2.0)
    x = (np.arange(nx) - (nx - 1) / 2.0)
    yy, xx = np.meshgrid(y, x, indexing='ij')
    r = np.hypot(xx, yy)
    K = 1.0 / np.where(r == 0.0, np.inf, r)
    K = np.fft.ifftshift(K)
    Ik = np.fft.rfftn(src)
    Kk = np.fft.rfftn(K)
    kappa = C * np.fft.irfftn(Ik * Kk, s=src.shape)
    # AICc on pixels
    m = np.isfinite(kappa_obs)
    N = int(np.sum(m))
    chi = float(np.nansum((kappa[m] - kappa_obs[m]) ** 2))  # proxy
    return aicc(chi, k=3, N=N)


def main() -> int:
    # training set placeholder: use bullet if no train maps
    maps = Path('data/cluster/maps'); fdb = Path('data/cluster/fdb')
    if not (maps / 'bullet_sigma_e.npy').exists():
        print('missing sigma_e; run maps/make_sigma_e.py')
        return 1
    # Build W,S for current alpha/beta defaults
    subprocess.run(['bash', '-lc', 'PYTHONPATH=. ./.venv/bin/python scripts/cluster/fdb/make_S_W.py'], check=False)
    W = np.load(fdb / 'bullet_W.npy'); S = np.load(fdb / 'bullet_S.npy')
    # Observed kappa (stub): if not provided, use normalized W*S convolved as a proxy target
    kappa_obs_path = Path('data/cluster/bullet/kappa.npy')
    if kappa_obs_path.exists():
        kappa_obs = np.load(kappa_obs_path)
        # resample to match W,S shape if needed
        if kappa_obs.shape != W.shape:
            import scipy.ndimage as ndi
            zy, zx = W.shape[0]/kappa_obs.shape[0], W.shape[1]/kappa_obs.shape[1]
            kappa_obs = ndi.zoom(kappa_obs, zoom=(zy, zx), order=1)
    else:
        from scripts.cluster.fdb.kappa_fdb import convolve_1_over_r
        kappa_obs = convolve_1_over_r(W * S)
        kappa_obs /= np.nanmax(np.abs(kappa_obs)) + 1e-12
    # Grid search
    best = (float('inf'), 0.0, 0.0, 1.0)
    for alpha in [0.0, 0.3, 1.0]:
        for beta in [0.0, 0.3]:
            for C in [0.5, 1.0, 2.0]:
                score = fit_one(kappa_obs, W, S, alpha, beta, C)
                if score < best[0]:
                    best = (score, alpha, beta, C)
    # include a placeholder scale (kpc/pix) for metrics; user should adjust per dataset (WCS)
    out = {
        'alpha': best[1], 'beta': best[2], 'C': best[3],
        'mu_k': {'epsilon': 1.0, 'k0': 0.2, 'm': 2}, 'gas_scale': 1.33,
        'scale_kpc_per_pix': 5.0
    }
    Path('data/cluster').mkdir(parents=True, exist_ok=True)
    Path('data/cluster/params_cluster.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('wrote params:', 'data/cluster/params_cluster.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
