#!/usr/bin/env python3
from __future__ import annotations
"""Build apparent acceleration from information-flow current J_I.

We provide a light 2D implementation that maps a scalar proxy map (e.g.,
Halpha SB or ω_cut) to a surface-normal field s(r) and a directional arrival
weight phi_dir(Ω; r) using forwardization, then integrates J_I and returns a
radial acceleration profile by circular-averaging the divergence.
"""
import numpy as np
from typing import Tuple
from theory.info_decoherence import integrate_JI, EtaParams


def forward_phi_dir_factory(forward_beta: float = 0.0, eps_smooth: float = 1.0) -> callable:
    """Construct phi_dir(Ωx,Ωy) based on local gradient magnitude and direction.

    Use |∇I| as a proxy of arrival intensity; forwardization will be encoded via
    eta (1+β cosθ). Here phi_dir is just |∇I| normalized.
    """
    grad_ref = {'gx': None, 'gy': None}
    def set_ref(gx: np.ndarray, gy: np.ndarray) -> None:
        grad_ref['gx'] = gx; grad_ref['gy'] = gy
    def phi_dir(Omx: np.ndarray, Omy: np.ndarray) -> np.ndarray:
        gx = grad_ref['gx']; gy = grad_ref['gy']
        if gx is None or gy is None:
            raise RuntimeError('phi_dir used before gradients set')
        mag = np.hypot(gx, gy)
        # light smoothing to avoid spiky weights
        if eps_smooth > 0:
            ky = np.fft.fftfreq(mag.shape[0])[:, None]
            kx = np.fft.fftfreq(mag.shape[1])[None, :]
            k2 = (2*np.pi)**2 * (ky*ky + kx*kx)
            H = np.exp(-0.5 * (eps_smooth**2) * k2)
            Mk = np.fft.fft2(np.nan_to_num(mag, nan=0.0))
            mag = np.fft.ifft2(Mk * H).real
        mag = np.clip(mag, 0.0, None)
        return mag
    phi_dir.set_ref = set_ref  # type: ignore
    return phi_dir


def info_bias_profile_from_map(R: np.ndarray, scalar_map: np.ndarray, pix_kpc: float,
                               k_grid: np.ndarray, phi_k: np.ndarray,
                               eta_params: EtaParams) -> np.ndarray:
    """Compute g_info(R) from a scalar proxy map (e.g., Halpha SB).

    Steps: compute gradients → unit surface vectors s(r) → integrate J_I →
    take divergence ∇·J_I → convolve with 1/r kernel via circular profile.
    """
    # gradients as surface proxy
    gy, gx = np.gradient(scalar_map.astype(float), pix_kpc)
    # reference for phi_dir
    phi_dir = forward_phi_dir_factory(eta_params.beta, eps_smooth=1.0)
    phi_dir.set_ref(gx, gy)
    # surface proxy unit vectors (in-plane)
    mag = np.hypot(gx, gy)
    mag = np.clip(mag, 1e-12, None)
    sx = gx / mag
    sy = gy / mag
    svec = np.dstack([sx, sy])
    # optional fixed radial phase profile φ0(R)=A(1-exp(-R/R0)) (no extra dof)
    phase_map = None
    if getattr(eta_params, 'phase_profile_base', 0.0) not in (None, 0.0):
        ny, nx = scalar_map.shape
        y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
        x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
        xx, yy = np.meshgrid(x, y, indexing='xy')
        rr = np.hypot(xx, yy)
        A = float(eta_params.phase_profile_base)
        R0 = float(getattr(eta_params, 'phase_profile_R0_kpc', 3.0))
        phase_map = A * (1.0 - np.exp(-rr / max(R0, 1e-6)))
    Jx, Jy = integrate_JI(phi_dir, k_grid, phi_k, svec, eta_params, phase_map=phase_map)
    # divergence
    dJx_dx = np.gradient(Jx, pix_kpc, axis=1)
    dJy_dy = np.gradient(Jy, pix_kpc, axis=0)
    divJ = dJx_dx + dJy_dy
    # convolve with 1/r kernel to get potential-like quantity → radial profile of |grad|
    ny, nx = divJ.shape
    ky = np.fft.fftfreq(ny)[:, None]
    kx = np.fft.fftfreq(nx)[None, :]
    k = np.sqrt((2*np.pi*ky)**2 + (2*np.pi*kx)**2)
    K = np.zeros_like(k)
    K[k > 0] = 1.0 / k[k > 0]  # ~ 1/|k| Fourier kernel corresponds to 1/r in real space
    Phi_k = np.fft.fft2(np.nan_to_num(divJ, nan=0.0)) * K
    pot = np.fft.ifft2(Phi_k).real
    # radial average of |∇pot|
    dpy, dpx = np.gradient(pot, pix_kpc)
    gmag = np.hypot(dpx, dpy)
    # circular bins
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    xx, yy = np.meshgrid(x, y, indexing='xy')
    rr = np.hypot(xx, yy)
    r_bins = np.linspace(0, rr.max(), 64)
    rb = 0.5 * (r_bins[:-1] + r_bins[1:])
    prof = np.zeros_like(rb)
    for i in range(len(rb)):
        m = (rr >= r_bins[i]) & (rr < r_bins[i+1]) & np.isfinite(gmag)
        if np.any(m):
            prof[i] = float(np.nanmean(gmag[m]))
        else:
            prof[i] = np.nan
    # map to target radii by interpolation
    left = float(prof[np.isfinite(prof)][0]) if np.isfinite(prof).any() else 0.0
    right = float(prof[np.isfinite(prof)][-1]) if np.isfinite(prof).any() else left
    gout = np.interp(R, rb, prof, left=left, right=right)
    return gout


def info_bias_vector_from_map(scalar_map: np.ndarray, pix_kpc: float,
                              k_grid: np.ndarray, phi_k: np.ndarray,
                              eta_params: EtaParams) -> tuple[np.ndarray, np.ndarray]:
    """Compute in‑plane acceleration vector a_info(x,y) from a scalar proxy map.

    Returns (ax, ay) on the same grid as scalar_map.
    """
    gy, gx = np.gradient(scalar_map.astype(float), pix_kpc)
    phi_dir = forward_phi_dir_factory(eta_params.beta, eps_smooth=1.0)
    phi_dir.set_ref(gx, gy)
    mag = np.hypot(gx, gy)
    mag = np.clip(mag, 1e-12, None)
    sx = gx / mag; sy = gy / mag
    svec = np.dstack([sx, sy])
    ny, nx = scalar_map.shape
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    xx, yy = np.meshgrid(x, y, indexing='xy')
    rr = np.hypot(xx, yy)
    phase_map = None
    if getattr(eta_params, 'phase_profile_base', 0.0) not in (None, 0.0):
        A = float(eta_params.phase_profile_base)
        R0 = float(getattr(eta_params, 'phase_profile_R0_kpc', 3.0))
        phase_map = A * (1.0 - np.exp(-rr / max(R0, 1e-6)))
    Jx, Jy = integrate_JI(phi_dir, k_grid, phi_k, svec, eta_params, phase_map=phase_map)
    dJx_dx = np.gradient(Jx, pix_kpc, axis=1)
    dJy_dy = np.gradient(Jy, pix_kpc, axis=0)
    divJ = dJx_dx + dJy_dy
    ny, nx = divJ.shape
    ky = np.fft.fftfreq(ny)[:, None]
    kx = np.fft.fftfreq(nx)[None, :]
    k = np.sqrt((2*np.pi*ky)**2 + (2*np.pi*kx)**2)
    K = np.zeros_like(k); K[k > 0] = 1.0 / k[k > 0]
    Phi_k = np.fft.fft2(np.nan_to_num(divJ, nan=0.0)) * K
    pot = np.fft.ifft2(Phi_k).real
    dpy, dpx = np.gradient(pot, pix_kpc)
    # apparent acceleration is gradient of potential
    ax = dpx; ay = dpy
    return ax, ay
