from __future__ import annotations
import numpy as np
from typing import Tuple


def smooth(field: np.ndarray, sigma: float | Tuple[float,float,float] | None) -> np.ndarray:
    if not sigma or (isinstance(sigma, (int,float)) and sigma <= 0):
        return field
    try:
        from scipy.ndimage import gaussian_filter
        return gaussian_filter(field, sigma)
    except Exception:
        return field


def omega_cut_from_proxy(proxy: np.ndarray, smooth_sigma: float | None = None) -> np.ndarray:
    # Treat proxy ∝ n_e; ω_p ∝ sqrt(n_e). Scale-free up to a constant factor.
    oc = np.sqrt(np.abs(proxy).astype(float))
    return smooth(oc, smooth_sigma)


def normals_and_H(omega_cut: np.ndarray, spacing: Tuple[float,float,float]) -> Tuple[np.ndarray,np.ndarray]:
    dz, dy, dx = spacing[2], spacing[1], spacing[0]
    gx = (np.roll(omega_cut, -1, axis=2) - np.roll(omega_cut, 1, axis=2)) / (2*dx)
    gy = (np.roll(omega_cut, -1, axis=1) - np.roll(omega_cut, 1, axis=1)) / (2*dy)
    gz = (np.roll(omega_cut, -1, axis=0) - np.roll(omega_cut, 1, axis=0)) / (2*dz)
    grad = np.stack([gx, gy, gz], axis=-1)
    gnorm = np.linalg.norm(grad, axis=-1, keepdims=True) + 1e-30
    n = -grad / gnorm  # decreasing ω_cut toward outside
    with np.errstate(divide='ignore', invalid='ignore'):
        H = 1.0 / (np.linalg.norm(np.stack([(gx/(omega_cut+1e-30)), (gy/(omega_cut+1e-30)), (gz/(omega_cut+1e-30))], axis=0), axis=0) + 1e-30)
    return n.astype(np.float32), H.astype(np.float32)


def thin_layer_delta(omega_cut: np.ndarray, omega_star: float, H: np.ndarray, c: float = 1.0) -> np.ndarray:
    # Smooth delta around ω_cut = ω* with width ε≈H
    eps = np.maximum(H, 1e-6)
    x = (omega_cut - float(omega_star)) / (eps + 1e-30)
    return (c / (np.sqrt(np.pi) * (eps + 1e-30))) * np.exp(-x*x)


def build_rho_eff_boundary(
    rho: np.ndarray,
    proxy: np.ndarray,
    spacing: Tuple[float,float,float],
    omega_star: float,
    alpha_esc: float,
    ell_star: float,
    smooth_sigma: float | None = None,
) -> Tuple[np.ndarray, dict]:
    oc = omega_cut_from_proxy(proxy, smooth_sigma)
    n, H = normals_and_H(oc, spacing)
    delta = thin_layer_delta(oc, omega_star, H)
    # Directional weighting placeholders: use scalar shell magnitude; orientation handled via separate anisotropic path.
    S = delta  # magnitude only; normalization captured by alpha_esc
    rho_eff = rho + float(alpha_esc) * S
    meta = {'omega_star': float(omega_star), 'alpha_esc': float(alpha_esc), 'ell_star': float(ell_star), 'smooth_sigma': float(smooth_sigma or 0.0)}
    return rho_eff.astype(float), meta

