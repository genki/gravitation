from __future__ import annotations
import numpy as np
from .constants import G, C
from .sph import real_sph_harm, lm_index


def _ahat_at_direction(a_lm: np.ndarray, lmax: int, rhat: np.ndarray) -> float:
    """Evaluate Â_y at direction rhat for a given voxel's coefficients a_lm[:].
    Uses Â = 1 + Σ_{l>=2} Σ_m a_{lm} Y_{lm}(rhat).
    """
    # Convert rhat (3,) to theta, phi
    x, y, z = rhat
    r = np.linalg.norm(rhat) + 1e-30
    theta = np.arccos(np.clip(z / r, -1.0, 1.0))
    phi = (np.arctan2(y, x) + 2*np.pi) % (2*np.pi)
    acc = 1.0
    for l in range(2, lmax+1):
        for m in range(-l, l+1):
            idx = l*l + (m + l)
            acc += a_lm[idx] * real_sph_harm(l, m, theta, phi)
    return float(acc)


def phi_eff_direct(
    x: np.ndarray,
    rho: np.ndarray,
    origin: tuple[float,float,float],
    spacing: tuple[float,float,float],
    a_lm_grid: np.ndarray | None = None,
    lmax: int = 0,
    eps: float = 0.0,
) -> float:
    """Direct-sum Φ_eff(x) = −G ∑ ρ(y) Â_y(r̂) / |x−y| dV. O(N) per x.

    a_lm_grid: (nz,ny,nx,L) or None. If None or lmax<2, uses isotropic Â=1.
    eps: softening (m) to avoid singularities at |x−y|→0.
    """
    nz, ny, nx = rho.shape
    dx, dy, dz = spacing
    x0, y0, z0 = origin
    xs = x0 + dx * (np.arange(nx) + 0.5)
    ys = y0 + dy * (np.arange(ny) + 0.5)
    zs = z0 + dz * (np.arange(nz) + 0.5)
    vol = dx * dy * dz
    acc = 0.0
    for iz, zz in enumerate(zs):
        for iy, yy in enumerate(ys):
            for ix, xx in enumerate(xs):
                rvec = x - np.array([xx, yy, zz])
                r = float(np.linalg.norm(rvec))
                if r < 1e-12:
                    continue
                ahat = 1.0
                if a_lm_grid is not None and lmax >= 2:
                    ahat = _ahat_at_direction(a_lm_grid[iz,iy,ix,:], lmax, rvec)
                acc += rho[iz,iy,ix] * ahat / np.sqrt(r*r + eps*eps)
    return -G * acc * vol


def lambda_direct(
    x: np.ndarray,
    rho: np.ndarray,
    origin: tuple[float,float,float],
    spacing: tuple[float,float,float],
    a_lm_grid: np.ndarray | None = None,
    lmax: int = 0,
    eps: float = 0.0,
) -> float:
    """Direct-sum Λ(x) = (G/c) ∑ ρ(y) Â_y(r̂) / |x−y|^2 dV. O(N) per x.
    """
    nz, ny, nx = rho.shape
    dx, dy, dz = spacing
    x0, y0, z0 = origin
    xs = x0 + dx * (np.arange(nx) + 0.5)
    ys = y0 + dy * (np.arange(ny) + 0.5)
    zs = z0 + dz * (np.arange(nz) + 0.5)
    vol = dx * dy * dz
    acc = 0.0
    for iz, zz in enumerate(zs):
        for iy, yy in enumerate(ys):
            for ix, xx in enumerate(xs):
                rvec = x - np.array([xx, yy, zz])
                r2 = float(np.dot(rvec, rvec) + eps*eps)
                if r2 < 1e-24:
                    continue
                ahat = 1.0
                if a_lm_grid is not None and lmax >= 2:
                    ahat = _ahat_at_direction(a_lm_grid[iz,iy,ix,:], lmax, rvec)
                acc += rho[iz,iy,ix] * ahat / r2
    # Λ = (G/c) ∫ ... = C * ∫ ... ; C already defined as G/c
    return C * acc * vol
