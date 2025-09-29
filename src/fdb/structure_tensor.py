from __future__ import annotations
import numpy as np


def gradients_central(rho: np.ndarray, spacing: tuple[float,float,float]) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    dz, dy, dx = spacing[2], spacing[1], spacing[0]
    gx = (np.roll(rho, -1, axis=2) - np.roll(rho, 1, axis=2)) / (2*dx)
    gy = (np.roll(rho, -1, axis=1) - np.roll(rho, 1, axis=1)) / (2*dy)
    gz = (np.roll(rho, -1, axis=0) - np.roll(rho, 1, axis=0)) / (2*dz)
    return gx, gy, gz


def structure_tensor(rho: np.ndarray, spacing: tuple[float,float,float], sigma: float | None = None) -> tuple[np.ndarray,np.ndarray]:
    """Compute per-voxel structure tensor and its eigen decomposition.

    Returns (eigvals, eigvecs) where eigvals: (nz,ny,nx,3), eigvecs: (nz,ny,nx,3,3)
    Eigvecs columns correspond to eigenvectors.
    """
    gx, gy, gz = gradients_central(rho, spacing)
    if sigma is not None and sigma > 0:
        try:
            from scipy.ndimage import gaussian_filter
            gx = gaussian_filter(gx, sigma)
            gy = gaussian_filter(gy, sigma)
            gz = gaussian_filter(gz, sigma)
        except Exception:
            pass
    nz, ny, nx = rho.shape
    eigvals = np.zeros((nz,ny,nx,3), dtype=np.float32)
    eigvecs = np.zeros((nz,ny,nx,3,3), dtype=np.float32)
    for iz in range(nz):
        for iy in range(ny):
            for ix in range(nx):
                g = np.array([gx[iz,iy,ix], gy[iz,iy,ix], gz[iz,iy,ix]], dtype=float)
                J = np.outer(g, g)
                w, V = np.linalg.eigh(J)
                order = np.argsort(w)[::-1]  # descending
                eigvals[iz,iy,ix,:] = w[order]
                eigvecs[iz,iy,ix,:,:] = V[:,order]
    return eigvals, eigvecs


def anisotropy_strengths(eigvals: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """Compute simple anisotropy strengths b_p from eigenvalues λ_p.
    b_p = (λ_p - mean(λ)) / (mean(λ) + eps), per voxel.
    Returns b of shape (nz,ny,nx,3) with sum(b_p)=0.
    """
    lam = eigvals
    mu = lam.mean(axis=-1, keepdims=True)
    b = (lam - mu) / (np.abs(mu) + eps)
    return b

