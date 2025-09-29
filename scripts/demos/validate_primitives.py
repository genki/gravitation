#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from fdb.grids import make_uniform_sphere, VoxelGrid
from fdb.integrators import phi_eff_direct
from fdb.constants import G


def analytic_uniform_sphere_potential(r: float, R: float, M: float) -> float:
    if r >= R:
        return -G * M / r
    # inside: −GM (3R^2 − r^2)/(2R^3)
    return -G * M * (3*R*R - r*r) / (2 * R**3)


def main():
    R = 1.0e3  # m
    rho0 = 1.0e-9  # kg/m^3 (arbitrary)
    dx = 50.0  # m
    grid = make_uniform_sphere(R, rho0, dx)
    nz, ny, nx = grid.rho.shape
    dx, dy, dz = grid.spacing
    vol = dx * dy * dz
    M = grid.rho.sum() * vol
    # sample points along x‑axis
    rs = np.linspace(0.25*R, 2.0*R, 8)
    points = np.stack([rs, np.zeros_like(rs), np.zeros_like(rs)], axis=1)
    phi_num = [phi_eff_direct(p, grid.rho, grid.origin, grid.spacing, None, 0, eps=0.25*dx) for p in points]
    phi_ana = [analytic_uniform_sphere_potential(r, R, M) for r in rs]
    phi_num = np.array(phi_num)
    phi_ana = np.array(phi_ana)
    rel_err = np.abs((phi_num - phi_ana) / np.maximum(1e-30, np.abs(phi_ana)))
    print("R=", R, "M=", M)
    for r, pn, pa, e in zip(rs, phi_num, phi_ana, rel_err):
        print(f"r={r:.2f} m  phi_num={pn:.6e}  phi_ana={pa:.6e}  rel_err={e:.3e}")
    ok = np.all(rel_err < 1e-2)
    print("PASS<=1%:", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

