"""
FDB anisotropic kernel (quadrupole extension) — theory scaffold.

K(r; n, alpha) = 1/r * [ 1 + alpha * g(r) * P2( rhat·n ) ]
with P2(u) = 0.5*(3u^2 - 1), angle-average zero, preserving isotropy for spheres.

This module provides small helpers for g(r) and P2/cosine utilities. Numerically,
we approximate the anisotropy in thin-disk axisymmetric use by P2(0) = -1/2.
"""
from __future__ import annotations
import numpy as np

def g_of_r(r: np.ndarray, ell0_kpc: float, m: int = 2) -> np.ndarray:
    r = np.asarray(r, dtype=float)
    if ell0_kpc <= 0:
        return np.zeros_like(r)
    return np.exp(- (np.abs(r) / float(ell0_kpc)) ** 2)

def P2(u: np.ndarray | float) -> np.ndarray | float:
    return 0.5 * (3.0 * np.asarray(u) ** 2 - 1.0)

