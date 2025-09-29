from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike
from scipy.special import i0, i1, k0, k1

# Physical constants (SI)
G: float = 6.67430e-11  # m^3 kg^-1 s^-2
C: float = 2.99792458e8  # m s^-1


def _as_array(x: ArrayLike) -> np.ndarray:
    return np.asarray(x, dtype=float)


def phi_point_mass(M: float, r: ArrayLike) -> np.ndarray:
    """Newtonian-like effective potential Phi_eff for a point mass.

    Phi(r) = - G M / r

    Parameters
    ----------
    M : float
        Mass [kg].
    r : ArrayLike
        Radius [m]. Broadcastable to numpy array.
    """
    r = _as_array(r)
    return -G * M / r


def accel_point_mass(M: float, pos: ArrayLike) -> np.ndarray:
    """Apparent acceleration a = -\nabla Phi_eff for a point mass at origin.

    Parameters
    ----------
    M : float
        Mass [kg].
    pos : ArrayLike
        Position vector(s) [m]; shape (..., D) with D=2 or 3.
    """
    rvec = _as_array(pos)
    r2 = np.sum(rvec * rvec, axis=-1, keepdims=True)
    r = np.sqrt(r2)
    # Avoid divide by zero
    eps = np.finfo(float).eps
    denom = (r2 * r + eps)
    return -G * M * rvec / denom


def u_info_mass(m: float, phi_eff: ArrayLike) -> np.ndarray:
    """Information potential for a massive test particle: U = m * Phi_eff."""
    return m * _as_array(phi_eff)


def u_info_photon(p: float, phi_eff: ArrayLike) -> np.ndarray:
    """Information potential for light: U = (p/c) * Phi_eff."""
    return (p / C) * _as_array(phi_eff)


def deflection_point_mass(M: float, b: ArrayLike) -> np.ndarray:
    """Weak-field light deflection by point mass using Phi_eff normalization.

    alpha_hat = 4 G M / (b c^2)
    """
    b = _as_array(b)
    return 4.0 * G * M / (b * C * C)


def v2_exponential_disk(R: ArrayLike, Sigma0: float, Rd: float) -> np.ndarray:
    """Freeman thin exponential disk rotation curve V^2(R).

    V^2(R) = 4 pi G Sigma0 Rd y^2 [I0(y) K0(y) - I1(y) K1(y)],
    y = R / (2 Rd)

    Parameters
    ----------
    R : ArrayLike
        Radius [m].
    Sigma0 : float
        Central surface density [kg m^-2].
    Rd : float
        Scale length [m].
    """
    R = _as_array(R)
    y = R / (2.0 * Rd)
    combo = i0(y) * k0(y) - i1(y) * k1(y)
    return 4.0 * np.pi * G * Sigma0 * Rd * (y * y) * combo

