from __future__ import annotations
"""
UVLF bright-end multiplicative boost from a growth-factor increase.

In Press–Schechter-like rare tail, number density scales roughly as
  n(>M) ~ exp(-ν^2/2), where ν = δ_c / (σ(M) D(a)).
If D → D' = rD, then ν' = ν / r and the ratio is
  R = n'(>M)/n(>M) = exp(-(ν'^2 - ν^2)/2) = exp( (ν^2/2) * (1 - 1/r^2) ).

This module provides helpers to compute R for given (ν, r) and to produce
simple visualization arrays for plotting.
"""

import numpy as np


def uvlf_multiplier(nu: np.ndarray | float, D_ratio: np.ndarray | float) -> np.ndarray:
    """Compute multiplicative factor R for given ν (peak height) and D_ratio = D'/D.

    Parameters
    - nu: peak height (≥ 1, typically 3–6 for bright-end at high z)
    - D_ratio: D'/D (e.g., 1.05 → 5% growth boost)
    """
    nu = np.asarray(nu, dtype=float)
    r = np.asarray(D_ratio, dtype=float)
    r2 = r * r
    return np.exp(0.5 * nu * nu * (1.0 - 1.0 / r2))


def grid_for_plot(nu_vals=(3.0, 4.0, 5.0, 6.0), D_ratios=(1.05, 1.10, 1.15)):
    nu = np.array(nu_vals, dtype=float)
    dr = np.array(D_ratios, dtype=float)
    # shape (len(dr), len(nu))
    R = np.vstack([uvlf_multiplier(nu, r) for r in dr])
    return nu, dr, R

