#!/usr/bin/env python3
from __future__ import annotations
"""UWM(=ULM) information-flow decoherence blocks.

Terminology mapping:
- UWM-P (propagating) ≈ ULM-h
- UWM-D (diffusive)  ≈ ULM-l

We model an information-arrival rate Phi(k, Ω; r) and a discriminability
kernel eta(k, Ω; s) (s: local surface/normal scale) and form
  J_I(r) = ∫ Phi · eta · Ω dk dΩ.

For minimal integration we provide:
 - eta_small_k: eta ≈ (k · Ω·s)^2 / 6 with optional phase kernel G(β)
 - quad_sphere: coarse angular quadrature over Ω
 - integrate_JI: build J_I on a 2D grid given Phi(k,Ω;r) factorized as
                  phi_k(k) * phi_dir(Ω; r) (simple factorization default)
"""
import numpy as np
from dataclasses import dataclass
from typing import Callable, Tuple


def eta_small_k(k: float, cos_theta: float, s: float, beta: float = 0.0) -> float:
    """eta ≈ (k (Ω·s))^2 / 6 with optional phase kernel G(β).

    cos_theta = Ω·ŝ (direction cosine between Ω and surface/normal proxy)
    s has units of length; k is 1/length.
    G(β) ~ 1 + β cos_theta (Lambert→forwardization; β=0 is Lambert).
    """
    base = (k * s * cos_theta) ** 2 / 6.0
    G = (1.0 + float(beta) * float(cos_theta))
    if G < 0:
        G = 0.0
    return float(base * G)


def quad_sphere(n_theta: int = 8, n_phi: int = 16) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (dirs, weights, cos_theta_grid) for unit directions.

    dirs: (M, 3) array of Ω vectors
    wts:  (M,) quadrature weights (~4π normalized)
    """
    thetas = np.linspace(1e-6, np.pi - 1e-6, n_theta)
    phis = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)
    dirs = []
    wts = []
    for th in thetas:
        sin_th = np.sin(th)
        for ph in phis:
            dirs.append([sin_th * np.cos(ph), sin_th * np.sin(ph), np.cos(th)])
            wts.append(sin_th)
    dirs = np.array(dirs, dtype=float)
    wts = np.array(wts, dtype=float)
    # Normalize weights to 4π
    wts *= (4.0 * np.pi) / np.sum(wts)
    return dirs, wts, thetas


@dataclass
class EtaParams:
    beta: float = 0.0  # phase kernel forwardization (0..1)
    s_kpc: float = 0.5  # effective surface scale [kpc]
    phase_shift: float = 0.0  # fixed interface-phase shift (radians); keeps k count unchanged
    phase_profile_base: float = 0.0  # base amplitude for fixed radial phase profile (no extra dof)
    phase_profile_R0_kpc: float = 3.0  # scale length for phase profile


def integrate_JI(phi_dir_fn: Callable[[np.ndarray, np.ndarray], np.ndarray],
                 k_grid: np.ndarray,
                 phi_k: np.ndarray,
                 svec_field: np.ndarray,
                 eta_params: EtaParams,
                 phase_map: np.ndarray | None = None) -> Tuple[np.ndarray, np.ndarray]:
    """Integrate J_I on a 2D grid.

    phi_dir_fn(Ωx, Ωy) -> (H, W) directional weight field for given direction.
    k_grid, phi_k: arrays defining ∫ phi_k(k) dk (simple Riemann sum)
    svec_field: (H, W, 2) local surface proxy unit vectors (in-plane)
    Returns (Jx, Jy) on the grid.
    """
    H, W, _ = svec_field.shape
    dirs, wts, _ = quad_sphere()
    # use only in-plane components for Ω (project to xy-plane)
    Om = dirs[:, :2]  # (M,2)
    w = wts.reshape(-1, 1, 1)  # (M,1,1)
    # integrate over k first
    phi_k_int = float(np.trapz(phi_k, k_grid))
    # initialize J
    Jx = np.zeros((H, W), dtype=float)
    Jy = np.zeros((H, W), dtype=float)
    svec = svec_field  # (H,W,2)
    s_norm = np.clip(np.sqrt((svec**2).sum(axis=2)), 1e-12, None)
    s_hat = svec / s_norm[..., None]
    for i in range(Om.shape[0]):
        Om_i = Om[i]  # (2,)
        cos_theta = (s_hat[..., 0] * Om_i[0] + s_hat[..., 1] * Om_i[1])  # (H,W)
        # optional fixed phase shift or profile (no extra fitted dof)
        if (phase_map is not None) or (eta_params.phase_shift != 0.0):
            ct = cos_theta
            st = np.sqrt(np.clip(1.0 - ct*ct, 0.0, None))
            if phase_map is not None:
                c0 = np.cos(phase_map); s0 = np.sin(phase_map)
            else:
                c0 = np.cos(float(eta_params.phase_shift)); s0 = np.sin(float(eta_params.phase_shift))
            cos_theta = ct * c0 - st * s0
        # eta averaged over k with small-k model (use mean k^2 factor)
        k2_mean = float(np.trapz((k_grid**2) * phi_k, k_grid) / (phi_k_int + 1e-30))
        eta = (k2_mean * (eta_params.s_kpc**2) * (cos_theta**2) / 6.0) * (1.0 + eta_params.beta * cos_theta)
        eta = np.clip(eta, 0.0, None)
        phi_dir = phi_dir_fn(np.full((H, W), Om_i[0]), np.full((H, W), Om_i[1]))
        contrib = w[i] * eta * phi_dir
        Jx += contrib * Om_i[0]
        Jy += contrib * Om_i[1]
    # multiply by integrated k-dependent factor
    Jx *= phi_k_int
    Jy *= phi_k_int
    return Jx, Jy
