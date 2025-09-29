#!/usr/bin/env python3
from __future__ import annotations
import json
import numpy as np
from pathlib import Path


def aicc(chi2: float, k: int, N: int) -> float:
    if N - k - 1 <= 0:
        return float('nan')
    return float(chi2 + 2 * k + (2 * k * (k + 1)) / (N - k - 1))


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


def load_params() -> dict:
    p = Path('data/cluster/params_cluster.json')
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'alpha': 0.0, 'beta': 0.0, 'C': 1.0}


def make_W_S(sigma_e: np.ndarray, alpha: float, beta: float) -> tuple[np.ndarray, np.ndarray]:
    wcut = np.sqrt(np.clip(sigma_e, 0.0, None))
    gx = (np.roll(wcut, -1, axis=1) - np.roll(wcut, 1, axis=1)) * 0.5
    gy = (np.roll(wcut, -1, axis=0) - np.roll(wcut, 1, axis=0)) * 0.5
    gnorm = np.sqrt(gx * gx + gy * gy) + 1e-12
    H = 1.0 / np.maximum(gnorm / np.maximum(wcut, 1e-12), 1e-12)
    wstar = float(np.nanmedian(wcut[np.isfinite(wcut)])) or 1.0
    delta = np.exp(-((wcut - wstar) ** 2) / (2.0 * (H * H))) / (np.sqrt(2.0 * np.pi) * np.maximum(H, 1e-12))
    ny, nx = sigma_e.shape
    y = (np.arange(ny) - (ny - 1) / 2.0)
    x = (np.arange(nx) - (nx - 1) / 2.0)
    yy, xx = np.meshgrid(y, x, indexing='ij')
    r = np.hypot(xx, yy)
    nxv = -gx / (gnorm + 1e-12); nyv = -gy / (gnorm + 1e-12)
    rx = xx / np.where(r == 0.0, np.inf, r); ry = yy / np.where(r == 0.0, np.inf, r)
    cosang = nxv * rx + nyv * ry
    G = (1.0 + float(beta) * cosang) / (1.0 + 0.5 * float(beta))
    W = np.exp(-float(alpha) * sigma_e)
    S = delta * np.maximum(cosang, 0.0) * G
    return W, S


def main() -> int:
    p = load_params(); alpha = float(p.get('alpha', 0.0)); beta = float(p.get('beta', 0.0)); C = float(p.get('C', 1.0))
    sigma = np.load('data/cluster/maps/bullet_sigma_e.npy')
    # observed kappa if present; else proxy from current params
    obs_path = Path('data/cluster/bullet/kappa.npy')
    if obs_path.exists():
        kappa_obs = np.load(obs_path)
    else:
        W, S = make_W_S(sigma, alpha, beta); kappa_obs = C * convolve_1_over_r(W * S)
        kappa_obs /= np.nanmax(np.abs(kappa_obs)) + 1e-12
    # resample observed kappa to sigma grid if needed
    if kappa_obs.shape != sigma.shape:
        import scipy.ndimage as ndi
        zy, zx = sigma.shape[0]/kappa_obs.shape[0], sigma.shape[1]/kappa_obs.shape[1]
        kappa_obs = ndi.zoom(kappa_obs, zoom=(zy, zx), order=1)

    # original model with current params
    W0, S0 = make_W_S(sigma, alpha, beta)
    kappa0 = C * convolve_1_over_r(W0 * S0)
    m = np.isfinite(kappa_obs)
    N = int(np.sum(m))
    chi0 = float(np.nansum((kappa0[m] - kappa_obs[m]) ** 2))
    a0 = aicc(chi0, 3, N)

    # rotation control (90 deg)
    sigma_r = np.rot90(sigma)
    Wr, Sr = make_W_S(sigma_r, alpha, beta)
    kappar = C * convolve_1_over_r(Wr * Sr)
    ar = aicc(float(np.nansum((kappar[m] - kappa_obs[m]) ** 2)), 3, N)

    # translation control (10% shift)
    sy = int(0.1 * sigma.shape[0]); sx = int(0.1 * sigma.shape[1])
    sigma_s = np.roll(np.roll(sigma, sy, axis=0), sx, axis=1)
    Ws, Ss = make_W_S(sigma_s, alpha, beta)
    kappas = C * convolve_1_over_r(Ws * Ss)
    aS = aicc(float(np.nansum((kappas[m] - kappa_obs[m]) ** 2)), 3, N)

    out = {
        'aicc_orig': a0,
        'rotate': {'aicc': ar, 'delta_aicc': ar - a0},
        'shift': {'aicc': aS, 'delta_aicc': aS - a0},
    }
    out_dir = Path('server/public/reports/cluster'); out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'bullet_control_tests.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('wrote', out_dir / 'bullet_control_tests.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
