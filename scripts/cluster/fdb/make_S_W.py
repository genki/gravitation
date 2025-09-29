#!/usr/bin/env python3
from __future__ import annotations
import json
import numpy as np
from pathlib import Path


def grad2(a: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    gx = (np.roll(a, -1, axis=1) - np.roll(a, 1, axis=1)) * 0.5
    gy = (np.roll(a, -1, axis=0) - np.roll(a, 1, axis=0)) * 0.5
    return gx, gy


def main() -> int:
    params = Path('data/cluster/params_cluster.json')
    if params.exists():
        P = json.loads(params.read_text(encoding='utf-8'))
        alpha = float(P.get('alpha', 0.0))
        beta = float(P.get('beta', 0.0))
    else:
        alpha = 0.0
        beta = 0.0
    sigma_e_path = Path('data/cluster/maps/bullet_sigma_e.npy')
    sigma_e = np.load(sigma_e_path)
    # ω_cut ~ sqrt(Σ_e)
    wcut = np.sqrt(np.clip(sigma_e, 0.0, None))
    # thickness scale H_cut ~ |∇ ln ω_cut|^{-1}
    gx, gy = grad2(wcut)
    gnorm = np.sqrt(gx * gx + gy * gy) + 1e-12
    H = 1.0 / np.maximum(gnorm / np.maximum(wcut, 1e-12), 1e-12)
    # Smooth delta around ω_* ~ median(wcut)
    wstar = float(np.nanmedian(wcut[np.isfinite(wcut)])) or 1.0
    delta = np.exp(-((wcut - wstar) ** 2) / (2.0 * (H * H))) / (np.sqrt(2.0 * np.pi) * np.maximum(H, 1e-12))
    # Angle kernel G(θ;β) ≈ 1 + β (n·r_hat)
    ny, nx = sigma_e.shape
    y = (np.arange(ny) - (ny - 1) / 2.0)
    x = (np.arange(nx) - (nx - 1) / 2.0)
    yy, xx = np.meshgrid(y, x, indexing='ij')
    r = np.hypot(xx, yy)
    # normal vector (pointing towards decreasing ω_cut)
    nxv = -gx / (gnorm + 1e-12)
    nyv = -gy / (gnorm + 1e-12)
    # radial unit
    rx = xx / np.where(r == 0.0, np.inf, r)
    ry = yy / np.where(r == 0.0, np.inf, r)
    cosang = nxv * rx + nyv * ry
    G = (1.0 + float(beta) * cosang) / (1.0 + 0.5 * float(beta))
    # W(θ) = exp(-α Σ_e)
    W = np.exp(-float(alpha) * sigma_e)
    # S(θ) = δ_ε * [n·r]_+ * G
    n_dot_r = np.maximum(cosang, 0.0)
    S = delta * n_dot_r * G
    out_dir = Path('data/cluster/fdb'); out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / 'bullet_W.npy', W)
    np.save(out_dir / 'bullet_S.npy', S)
    np.save(out_dir / 'bullet_wcut.npy', wcut)
    print('wrote W,S to', out_dir)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

