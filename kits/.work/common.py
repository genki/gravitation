
from __future__ import annotations
import numpy as np

# Physical constants (SI)
G = 6.67430e-11
c = 299_792_458.0
AU = 1.495978707e11
R_sun = 6.957e8
pi = np.pi

def hd_curve(theta_rad: np.ndarray) -> np.ndarray:
    """Hellings–Downs correlation curve for distinct pulsar pairs (TT-only, normalized).
    theta_rad: array of angles between pulsars [rad].
    Returns: ζ(θ) in the common normalized form (distinct pairs; no delta_ij term).
    ζ(θ) = (3/2) x ln x - 1/4 x + 1/2,  with x = (1 - cos θ)/2.
    """
    th = np.asarray(theta_rad, dtype=float)
    x = (1.0 - np.cos(th)) * 0.5
    # avoid log(0) at θ=0 by clipping x to tiny positive
    x = np.clip(x, 1e-16, 1.0)
    zeta = 1.5 * x * np.log(x) - 0.25 * x + 0.5
    return zeta

def flat_scalar_correlation(theta_rad: np.ndarray) -> np.ndarray:
    """A placeholder alternative correlation shape (angle-independent 'flat' mode).
    This is NOT claiming the exact scalar-breathing curve; it is a neutral basis shape
    useful for sensitivity studies. Users can replace with any alternative shape.
    """
    return np.ones_like(theta_rad) * 0.5

def rms(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    return float(np.sqrt(np.mean(x**2)))
