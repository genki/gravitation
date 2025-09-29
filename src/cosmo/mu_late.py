from __future__ import annotations
"""
Late-FDB effective gravity multiplier mu_late(a, k).

Definitions
- mu_late(a,k) = 1 + eps(a) * S(k)
- eps(a) = eps_max * sigma((a - a_on)/da), where sigma(x) = 1/(1+exp(-x))
- S(k) = k^2 / (k^2 + k_c^2) to suppress super-horizon / large-scale modes

Notes
- a: scale factor (0< a <= 1). Accepts float or ndarray.
- k: comoving wavenumber in 1/Mpc (or consistent units). Accepts float or ndarray.
- All operations are vectorized with NumPy broadcasting.
"""

import numpy as np


def logistic(x: np.ndarray | float) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    # Clip to avoid overflow in exp
    x = np.clip(x, -60.0, 60.0)
    return 1.0 / (1.0 + np.exp(-x))


def eps_of_a(
    a: np.ndarray | float,
    eps_max: float = 0.1,
    a_on: float = 1.0 / 21.0,  # z≈20
    da: float = 0.02,
) -> np.ndarray:
    """Smooth turn-on function eps(a).

    Parameters
    - a_on: midpoint of activation (scale factor)
    - da  : width of transition (in a)
    """
    a = np.asarray(a, dtype=float)
    return float(eps_max) * logistic((a - float(a_on)) / max(float(da), 1e-9))


def shape_S_of_k(k: np.ndarray | float, k_c: float = 0.2) -> np.ndarray:
    """Shape kernel S(k) = k^2/(k^2 + k_c^2).

    Parameters
    - k_c: cutoff scale; corresponds to characteristic radius ~ 2π/k_c
    """
    k = np.asarray(k, dtype=float)
    kc2 = max(float(k_c), 1e-12) ** 2
    kk = np.maximum(k, 0.0)
    return (kk * kk) / (kk * kk + kc2)


def mu_late(
    a: np.ndarray | float,
    k: np.ndarray | float,
    eps_max: float = 0.1,
    a_on: float = 1.0 / 21.0,
    da: float = 0.02,
    k_c: float = 0.2,
    *,
    k_sup: float | None = None,
    n_sup: float = 2.0,
) -> np.ndarray:
    """Compute mu_late(a,k) with broadcasting.

    Returns an array with shape = broadcast(a, k).
    """
    ea = eps_of_a(a, eps_max=eps_max, a_on=a_on, da=da)
    sk = shape_S_of_k(k, k_c=k_c)
    # Let NumPy broadcasting handle shapes like (A,1) * (1,K) → (A,K)
    suppress = 1.0
    if k_sup is not None and float(k_sup) > 0.0:
        ks = float(k_sup)
        ns = max(float(n_sup), 1.0)
        suppress = np.exp(-np.power(np.maximum(k, 0.0) / ks, ns))
    return 1.0 + (ea * sk * suppress)
