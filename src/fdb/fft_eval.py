from __future__ import annotations
import numpy as np
from .mu0 import kgrid, mu0_of_k


def phi_eff_fft_iso(rho: np.ndarray, spacing: tuple[float,float,float], eps: float = 0.0) -> np.ndarray:
    """Isotropic Φ_eff via FFT convolution with Green's function −G/|r|.

    Returns Φ grid same shape as rho. This ignores Â (assumes Â=1) and uses
    zero‑padded periodic convolution approximation. For validation only.
    """
    from .constants import G
    dz, dy, dx = spacing[2], spacing[1], spacing[0]
    nz, ny, nx = rho.shape
    pad = [nz, ny, nx]
    Nz, Ny, Nx = nz+pad[0], ny+pad[1], nx+pad[2]
    rho_pad = np.zeros((Nz, Ny, Nx), dtype=float)
    rho_pad[:nz,:ny,:nx] = rho
    # build kernel 1/r on same padded grid centered at (0,0,0)
    z = (np.arange(Nz) - 0) * dz
    y = (np.arange(Ny) - 0) * dy
    x = (np.arange(Nx) - 0) * dx
    Z, Y, X = np.meshgrid(z, y, x, indexing='ij')
    R = np.sqrt(X**2 + Y**2 + Z**2 + (eps*eps))
    kern = -G / np.where(R>0, R, np.inf)
    # FFT‑based convolution
    F_rho = np.fft.rfftn(rho_pad)
    F_k = np.fft.rfftn(kern)
    Phi = np.fft.irfftn(F_rho * F_k, s=rho_pad.shape)
    # crop to original domain
    return Phi[:nz,:ny,:nx]


def phi_eff_fft_iso_mu(
    rho: np.ndarray,
    spacing: tuple[float,float,float],
    eps: float = 0.0,
    eps_mu: float = 0.0,
    k0: float = 1.0,
    m: float = 2.0,
) -> np.ndarray:
    from .constants import G
    nz, ny, nx = rho.shape
    pad = [nz, ny, nx]
    Nz, Ny, Nx = nz+pad[0], ny+pad[1], nx+pad[2]
    rho_pad = np.zeros((Nz, Ny, Nx), dtype=float)
    rho_pad[:nz,:ny,:nx] = rho
    F_rho = np.fft.fftn(rho_pad)
    KX, KY, KZ, K = kgrid(rho_pad.shape, spacing)
    with np.errstate(divide='ignore', invalid='ignore'):
        kern_k = -4*np.pi*G * mu0_of_k(K, eps_mu, k0, m) / np.where(K>0, K*K, np.inf)
        kern_k[0,0,0] = 0.0
    Phi = np.fft.ifftn(F_rho * kern_k).real
    return Phi[:nz,:ny,:nx]


def phi_eff_fft_l2(
    rho: np.ndarray,
    a2: np.ndarray,
    spacing: tuple[float,float,float],
    n_hat: tuple[float,float,float] = (0.0, 0.0, 1.0),
    eps: float = 0.0,
) -> np.ndarray:
    """Anisotropic (l=2) correction Φ2 via FFT convolution.

    Uses kernel K(r) = -G * ((cos^2(theta) - 1/3) / |r|), where cos(theta)=r̂·n_hat.
    Assumes global principal axis n_hat. Convolves K with q = rho * a2.
    Returns Φ2 grid same shape as rho.
    """
    from .constants import G
    assert rho.shape == a2.shape
    dz, dy, dx = spacing[2], spacing[1], spacing[0]
    nz, ny, nx = rho.shape
    pad = [nz, ny, nx]
    Nz, Ny, Nx = nz+pad[0], ny+pad[1], nx+pad[2]
    rho_pad = np.zeros((Nz, Ny, Nx), dtype=float)
    rho_pad[:nz,:ny,:nx] = (rho * a2)
    # kernel on padded grid centered at (0,0,0)
    z = (np.arange(Nz) - 0) * dz
    y = (np.arange(Ny) - 0) * dy
    x = (np.arange(Nx) - 0) * dx
    Z, Y, X = np.meshgrid(z, y, x, indexing='ij')
    R = np.sqrt(X**2 + Y**2 + Z**2 + (eps*eps))
    # avoid singularity at origin
    with np.errstate(invalid='ignore', divide='ignore'):
        nx_, ny_, nz_ = n_hat
        dot = (X*nx_ + Y*ny_ + Z*nz_)
        cos2 = np.where(R>0, (dot / R)**2, 0.0)
        kern = -G * ((cos2 - (1.0/3.0)) / np.where(R>0, R, np.inf))
        kern[0,0,0] = 0.0
    F_q = np.fft.fftn(rho_pad)
    F_k = np.fft.fftn(kern)
    Phi2 = np.fft.ifftn(F_q * F_k).real
    return Phi2[:nz,:ny,:nx]


def phi_eff_fft_l2_mu(
    rho: np.ndarray,
    a2: np.ndarray,
    spacing: tuple[float,float,float],
    n_hat: tuple[float,float,float] = (0.0, 0.0, 1.0),
    eps: float = 0.0,
    eps_mu: float = 0.0,
    k0: float = 1.0,
    m: float = 2.0,
) -> np.ndarray:
    """Anisotropic (l=2) Φ2 with μ0(k) multiplier in k-space.

    Builds real-space kernel K(r) and FFTs it, then multiplies by μ0(k) before applying to source q=rho*a2.
    """
    nz, ny, nx = rho.shape
    pad = [nz, ny, nx]
    Nz, Ny, Nx = nz+pad[0], ny+pad[1], nx+pad[2]
    rho_pad = np.zeros((Nz, Ny, Nx), dtype=float)
    rho_pad[:nz,:ny,:nx] = (rho * a2)
    # build kernel
    dz, dy, dx = spacing[2], spacing[1], spacing[0]
    z = (np.arange(Nz) - 0) * dz
    y = (np.arange(Ny) - 0) * dy
    x = (np.arange(Nx) - 0) * dx
    Z, Y, X = np.meshgrid(z, y, x, indexing='ij')
    R = np.sqrt(X**2 + Y**2 + Z**2 + (eps*eps))
    nx_, ny_, nz_ = n_hat
    dot = (X*nx_ + Y*ny_ + Z*nz_)
    cos2 = np.where(R>0, (dot / R)**2, 0.0)
    from .constants import G
    kern = -G * ((cos2 - (1.0/3.0)) / np.where(R>0, R, np.inf))
    kern[0,0,0] = 0.0
    # FFTs
    F_q = np.fft.fftn(rho_pad)
    F_k = np.fft.fftn(kern)
    # μ0(k) multiplier
    _, _, _, K = kgrid(rho_pad.shape, spacing)
    MU = mu0_of_k(K, eps_mu, k0, m)
    Phi2 = np.fft.ifftn(F_q * F_k * MU).real
    return Phi2[:nz,:ny,:nx]
