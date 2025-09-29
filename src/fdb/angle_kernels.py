from __future__ import annotations
import numpy as np


def beta_of_chi(chi: float) -> float:
    return float(min(1.0, np.sqrt(max(0.0, chi))))


def K_lambert_forward(cos_theta: np.ndarray, chi: float) -> np.ndarray:
    # K(θ;χ) = [cosθ/π] · (1+β cosθ)/(1+β/2), β=min{1,√χ}
    beta = beta_of_chi(chi)
    num = (1.0 + beta * cos_theta)
    den = (1.0 + 0.5 * beta)
    return (np.maximum(cos_theta, 0.0) / np.pi) * (num / den)


def hemisphere_normalization_error(chi: float, nsamp: int = 200000) -> float:
    # Monte Carlo over hemisphere to check ∫ K dΩ = 1
    u = np.random.rand(nsamp)
    v = np.random.rand(nsamp)
    # sample hemisphere: cosθ∈[0,1], φ∈[0,2π)
    cos_theta = u
    phi = 2*np.pi*v
    K = K_lambert_forward(cos_theta, chi)
    # dΩ = sinθ dθ dφ = d(cosθ) dφ
    integral = np.mean(K) * (1.0) * (2*np.pi)
    return float(abs(integral - 1.0))

def radial_forwardize(R: np.ndarray, g: np.ndarray, beta: float) -> np.ndarray:
    """
    Forwardization proxy for radial-only profiles.
    Emphasizes larger radii proportionally to β in [0,1].
    g'(R) = g(R) * (1 + β * (R - Rmin)/(Rmax - Rmin)).
    """
    if beta is None or beta <= 0.0:
        return g
    R = np.asarray(R); g = np.asarray(g)
    rmin = float(np.nanmin(R)); rmax = float(np.nanmax(R))
    span = max(rmax - rmin, 1e-12)
    w = 1.0 + float(max(0.0, min(1.0, beta))) * (R - rmin) / span
    return g * w
