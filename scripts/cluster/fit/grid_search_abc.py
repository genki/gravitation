#!/usr/bin/env python3
from __future__ import annotations
import json
import numpy as np
from pathlib import Path


def convolve_1_over_r(img: np.ndarray) -> np.ndarray:
    ny, nx = img.shape
    y = (np.arange(ny) - (ny - 1) / 2.0)
    x = (np.arange(nx) - (nx - 1) / 2.0)
    yy, xx = np.meshgrid(y, x, indexing='ij')
    r = np.hypot(xx, yy)
    K = 1.0 / np.where(r == 0.0, np.inf, r)
    K = np.fft.ifftshift(K)
    Ik = np.fft.rfftn(img)
    Kk = np.fft.rfftn(K)
    return np.fft.irfftn(Ik * Kk, s=img.shape)


def build_W_S(sigma: np.ndarray, alpha: float, beta: float) -> tuple[np.ndarray, np.ndarray]:
    wcut = np.sqrt(np.clip(sigma, 0.0, None))
    gx = (np.roll(wcut, -1, axis=1) - np.roll(wcut, 1, axis=1)) * 0.5
    gy = (np.roll(wcut, -1, axis=0) - np.roll(wcut, 1, axis=0)) * 0.5
    gnorm = np.sqrt(gx * gx + gy * gy) + 1e-12
    H = 1.0 / np.maximum(gnorm / np.maximum(wcut, 1e-12), 1e-12)
    wstar = float(np.nanmedian(wcut[np.isfinite(wcut)])) or 1.0
    delta = np.exp(-((wcut - wstar) ** 2) / (2.0 * (H * H))) / (np.sqrt(2.0 * np.pi) * np.maximum(H, 1e-12))
    ny, nx = sigma.shape
    y = (np.arange(ny) - (ny - 1) / 2.0)
    x = (np.arange(nx) - (nx - 1) / 2.0)
    yy, xx = np.meshgrid(y, x, indexing='ij')
    r = np.hypot(xx, yy)
    nxv = -gx / (gnorm + 1e-12); nyv = -gy / (gnorm + 1e-12)
    rx = xx / np.where(r == 0.0, np.inf, r); ry = yy / np.where(r == 0.0, np.inf, r)
    cosang = nxv * rx + nyv * ry
    G = (1.0 + float(beta) * cosang) / (1.0 + 0.5 * float(beta))
    W = np.exp(-float(alpha) * sigma)
    S = delta * np.maximum(cosang, 0.0) * G
    return W, S


def aicc(chi2: float, k: int, N: int) -> float:
    return float(chi2 + (2*k*(k+1))/max(N-k-1,1))


def main() -> int:
    # inputs
    obs = np.load('data/cluster/bullet/kappa.npy')  # observed kappa on target grid
    sigma = np.load('data/cluster/maps/bullet_sigma_e_kappa.npy') if Path('data/cluster/maps/bullet_sigma_e_kappa.npy').exists() else np.load('data/cluster/maps/bullet_sigma_e.npy')
    # resample sigma to obs shape
    if sigma.shape != obs.shape:
        import scipy.ndimage as ndi
        zy, zx = obs.shape[0]/sigma.shape[0], obs.shape[1]/sigma.shape[1]
        sigma = ndi.zoom(sigma, zoom=(zy, zx), order=1)
    # GR(baryon) proxy
    try:
        kappa_gr = np.load('data/cluster/gr/bullet_kappa_gr.npy')
        if kappa_gr.shape != obs.shape:
            import scipy.ndimage as ndi
            zy, zx = obs.shape[0]/kappa_gr.shape[0], obs.shape[1]/kappa_gr.shape[1]
            kappa_gr = ndi.zoom(kappa_gr, zoom=(zy, zx), order=1)
    except Exception:
        kappa_gr = np.zeros_like(obs)

    # coarse→fine grids
    alpha_grid = [0.0, 0.5, 1.0, 1.5, 2.0]
    beta_grid  = [0.0, 0.2, 0.4, 0.6]
    C_grid     = [0.1, 0.2, 0.5, 1.0, 2.0]
    best = (float('inf'), 0.0, 0.0, 1.0)
    N = int(np.isfinite(obs).sum()) or obs.size
    for a in alpha_grid:
        for b in beta_grid:
            W, S = build_W_S(sigma, a, b)
            base = convolve_1_over_r(W * S)
            for C in C_grid:
                kappa_tot = kappa_gr + C * base
                chi = float(np.nansum((kappa_tot - obs) ** 2))
                score = aicc(chi, k=3, N=N)
                if score < best[0]:
                    best = (score, a, b, C)
    # local refine around best
    a0, b0, c0 = best[1], best[2], best[3]
    a_list = np.linspace(max(0.0, a0-0.5), a0+0.5, 5)
    b_list = np.linspace(max(0.0, b0-0.2), min(1.0, b0+0.2), 5)
    c_list = np.geomspace(max(0.05, c0/2), c0*2, 5)
    for a in a_list:
        for b in b_list:
            W, S = build_W_S(sigma, float(a), float(b))
            base = convolve_1_over_r(W * S)
            for C in c_list:
                kappa_tot = kappa_gr + float(C) * base
                chi = float(np.nansum((kappa_tot - obs) ** 2))
                score = aicc(chi, k=3, N=N)
                if score < best[0]:
                    best = (score, float(a), float(b), float(C))
    # write params
    params_p = Path('data/cluster/params_cluster.json')
    P = {}
    if params_p.exists():
        P = json.loads(params_p.read_text(encoding='utf-8'))
    P.update({'alpha': best[1], 'beta': best[2], 'C': best[3]})
    params_p.write_text(json.dumps(P, indent=2), encoding='utf-8')
    print('best AICc:', best[0], 'alpha=', best[1], 'beta=', best[2], 'C=', best[3])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

