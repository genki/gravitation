#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
import numpy as np
from fdb.grids import make_thin_disk
from fdb.fft_eval import phi_eff_fft_iso_mu, phi_eff_fft_l2_mu


def v_c(phi: np.ndarray, spacing: tuple[float,float,float]) -> tuple[np.ndarray,np.ndarray]:
    nz, ny, nx = phi.shape
    dx = spacing[0]
    zc = nz//2; yc = ny//2
    # central differences along x
    dphidx = (phi[zc,yc,2:] - phi[zc,yc,:-2])/(2*dx)
    xs = np.arange(1, nx-1)
    R = (xs[1:-1] - xs.mean()*0) * dx
    gR = -dphidx[1:-1]
    return R, np.sqrt(np.maximum(gR*R, 0.0))


def main() -> int:
    ap = argparse.ArgumentParser(description='Sensitivity of v_c to (a2, eps, k0) around baseline')
    ap.add_argument('--R', type=float, default=16.0)
    ap.add_argument('--h', type=float, default=4.0)
    ap.add_argument('--rho0', type=float, default=1.0)
    ap.add_argument('--dx', type=float, default=1.0)
    ap.add_argument('--eps', type=float, default=1.0)
    ap.add_argument('--k0', type=float, default=0.2)
    ap.add_argument('--m', type=float, default=2.0)
    ap.add_argument('--a2', type=float, default=0.3)
    ap.add_argument('--delta', type=float, default=0.05, help='fractional perturbation')
    args = ap.parse_args()
    grid = make_thin_disk(R=args.R, h=args.h, rho0=args.rho0, spacing=args.dx)
    rho = grid.rho
    # baseline
    phi0 = phi_eff_fft_iso_mu(rho, grid.spacing, eps=1e-3, eps_mu=args.eps, k0=args.k0, m=args.m)
    phi2 = phi_eff_fft_l2_mu(rho, np.zeros_like(rho)+args.a2, grid.spacing, n_hat=(0,0,1), eps=1e-3, eps_mu=args.eps, k0=args.k0, m=args.m)
    R, v = v_c(phi0+phi2, grid.spacing)
    # perturbed parameters
    de = max(1e-6, args.delta*args.eps)
    dk = max(1e-6, args.delta*args.k0)
    da = max(1e-6, args.delta*args.a2)
    v_de = v_c(phi_eff_fft_iso_mu(rho, grid.spacing, 1e-3, args.eps+de, args.k0, args.m)
               + phi_eff_fft_l2_mu(rho, np.zeros_like(rho)+args.a2, grid.spacing, (0,0,1), 1e-3, args.eps+de, args.k0, args.m), grid.spacing)[1]
    v_dk = v_c(phi_eff_fft_iso_mu(rho, grid.spacing, 1e-3, args.eps, args.k0+dk, args.m)
               + phi_eff_fft_l2_mu(rho, np.zeros_like(rho)+args.a2, grid.spacing, (0,0,1), 1e-3, args.eps, args.k0+dk, args.m), grid.spacing)[1]
    v_da = v_c(phi0 + phi_eff_fft_l2_mu(rho, np.zeros_like(rho)+(args.a2+da), grid.spacing, (0,0,1), 1e-3, args.eps, args.k0, args.m), grid.spacing)[1]
    # sensitivities at each radius
    Se = (v_de - v) / de
    Sk = (v_dk - v) / dk
    Sa = (v_da - v) / da
    # correlation / condition number proxy
    X = np.vstack([Sa, Se, Sk]).T  # [radii x params]
    # normalize columns
    Xn = X / (np.linalg.norm(X, axis=0, keepdims=True) + 1e-12)
    G = Xn.T @ Xn
    evals = np.linalg.eigvalsh(G)
    cond = float((evals.max()+1e-12)/(evals.min()+1e-12))
    out = {
        'radii': R.tolist(),
        'sens': {'a2': Sa.tolist(), 'eps': Se.tolist(), 'k0': Sk.tolist()},
        'gram_evals': evals.tolist(),
        'condition_number': cond
    }
    print(json.dumps(out)[:1000])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

