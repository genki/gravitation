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
    out = np.fft.irfftn(Ik * Kk, s=img.shape)
    return out


def main() -> int:
    params = Path('data/cluster/params_cluster.json')
    if params.exists():
        P = json.loads(params.read_text(encoding='utf-8'))
        C = float(P.get('C', 1.0))
    else:
        C = 1.0
    # Prefer sigma_e regridded to kappa shape if available
    sigma_k = Path('data/cluster/maps/bullet_sigma_e_kappa.npy')
    if sigma_k.exists():
        sigma = np.load(sigma_k)
        # build W,S inline to ensure matching shape
        alpha = float(P.get('alpha', 0.0)); beta = float(P.get('beta', 0.0))
        # reuse logic from make_S_W
        def grad2(a):
            gx = (np.roll(a, -1, axis=1) - np.roll(a, 1, axis=1)) * 0.5
            gy = (np.roll(a, -1, axis=0) - np.roll(a, 1, axis=0)) * 0.5
            return gx, gy
        wcut = np.sqrt(np.clip(sigma, 0.0, None))
        gx, gy = grad2(wcut)
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
        G = (1.0 + float(P.get('beta', 0.0)) * cosang) / (1.0 + 0.5 * float(P.get('beta', 0.0)))
        W = np.exp(-float(P.get('alpha', 0.0)) * sigma)
        S = delta * np.maximum(cosang, 0.0) * G
    else:
        Wp = Path('data/cluster/fdb/bullet_W.npy')
        Sp = Path('data/cluster/fdb/bullet_S.npy')
        if not (Wp.exists() and Sp.exists()):
            print('missing W/S; run make_S_W.py')
            return 1
        W = np.load(Wp); S = np.load(Sp)
    src = W * S
    kappa_fdb = C * convolve_1_over_r(src)
    out_dir = Path('data/cluster/fdb'); out_dir.mkdir(parents=True, exist_ok=True)
    np.save(out_dir / 'bullet_kappa_fdb.npy', kappa_fdb)
    print('wrote', out_dir / 'bullet_kappa_fdb.npy')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
