from __future__ import annotations
"""
Linear growth solver with Late-FDB mu_late(a,k).

We solve for D(a,k) using the standard growth ODE in ln a:
  d2D/d(ln a)^2 + [2 + d ln H / d ln a] dD/d(ln a) - (3/2) Ω_m(a) μ(a,k) D = 0

Assumptions
- Flat ΛCDM background (Ω_m0 + Ω_Λ0 = 1). Radiation ignored for simplicity at z≲100.
- Units: a in [~0.01, 1], k in 1/Mpc (consistent with μ definition).

This module provides:
- growth_factor(a_grid, k, params) → D(a)/D(a_ref)
- convenience wrappers for baseline ΛCDM (μ=1) and Late-FDB μ(a,k)
"""

from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp

from .mu_late import mu_late


@dataclass
class Cosmology:
    Om0: float = 0.315
    Ol0: float = 0.685

    def E2(self, a: float) -> float:
        a = float(a)
        return self.Om0 * a ** (-3) + self.Ol0

    def dlnH_dlna(self, a: float) -> float:
        # H^2 ∝ E2(a), so ln H = 0.5 ln E2
        Om_a = self.Om0 * a ** (-3) / self.E2(a)
        Ol_a = self.Ol0 / self.E2(a)
        # d ln H / d ln a = -3/2 * Ω_m(a)
        return -1.5 * Om_a

    def Om_of_a(self, a: float) -> float:
        return self.Om0 * a ** (-3) / self.E2(a)


def _growth_rhs(ln_a: float, y: np.ndarray, cosmo: Cosmology, mu_val: float) -> np.ndarray:
    # y = [D, dD/d ln a]
    a = float(np.exp(ln_a))
    Om = cosmo.Om_of_a(a)
    A = 2.0 + cosmo.dlnH_dlna(a)
    B = 1.5 * Om * mu_val
    D, F = y
    dD_dla = F
    dF_dla = -A * F + B * D
    return np.array([dD_dla, dF_dla], dtype=float)


def growth_factor(
    a_grid: np.ndarray,
    k: float,
    cosmo: Cosmology | None = None,
    use_mu_late: bool = True,
    eps_max: float = 0.1,
    a_on: float = 1.0 / 21.0,
    da: float = 0.02,
    k_c: float = 0.2,
    k_sup: float | None = None,
    n_sup: float = 2.0,
    a_init: float | None = None,
) -> np.ndarray:
    """Compute D(a,k) normalized to D(a_ref) where a_ref = max(a_init, first a_grid).

    Notes
    - Uses a quasi-constant μ(a,k) per step via midpoint evaluation for stability.
    - For speed and robustness, integrate once with μ evaluated at representative k.
    """
    if cosmo is None:
        cosmo = Cosmology()
    a_grid = np.asarray(a_grid, dtype=float)
    if a_grid.ndim != 1:
        raise ValueError("a_grid must be 1D increasing")
    if not np.all(np.diff(a_grid) > 0):
        raise ValueError("a_grid must be strictly increasing")
    a0 = float(a_init or a_grid[0])
    ln_a0 = np.log(a0)
    ln_a1 = np.log(a_grid[-1])

    # Effective μ(a,k): evaluate on fine subgrid for accuracy
    a_sub = np.geomspace(max(a0, 1e-4), a_grid[-1], 256)
    if use_mu_late:
        mu_sub = np.squeeze(
            mu_late(
                a_sub,
                k,
                eps_max=eps_max,
                a_on=a_on,
                da=da,
                k_c=k_c,
                k_sup=k_sup,
                n_sup=n_sup,
            )
        )
    else:
        mu_sub = np.ones_like(a_sub)

    # Integrate ODE with μ(a) interpolated in ln a
    ln_a_sub = np.log(a_sub)
    def mu_at(a_val: float) -> float:
        return float(np.interp(np.log(a_val), ln_a_sub, mu_sub))

    def rhs(ln_a: float, y: np.ndarray) -> np.ndarray:
        a_mid = float(np.exp(ln_a))
        return _growth_rhs(ln_a, y, cosmo, mu_at(a_mid))

    # Initial conditions: growing mode ~ a in matter era → set D=a, dD/dln a = D
    D0 = a0
    y0 = np.array([D0, D0], dtype=float)
    sol = solve_ivp(rhs, (ln_a0, ln_a1), y0, method="RK45", rtol=1e-5, atol=1e-7, dense_output=True)
    if not sol.success:
        raise RuntimeError(f"growth ODE failed: {sol.message}")
    D_vals = sol.sol(np.log(a_grid))[0]
    # Normalize to D(a_ref = first a on grid)
    ref = float(D_vals[0]) if D_vals[0] != 0 else 1.0
    return np.asarray(D_vals) / ref

