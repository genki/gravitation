"""
Shape-tensor (tidal) scaffold.

Computes a simple tidal tensor Q_ij from a Newtonian potential Phi_N on a grid.
Here we provide a placeholder that yields zeros (sphere) or a disk-like director
along z for axisymmetric thin-disk inputs (by heuristic), to keep the pipeline
stable until full 3D implementation.
"""
from __future__ import annotations
import numpy as np

def tidal_Q_from_disk_axes(nx: int, ny: int, nz: int = 1) -> np.ndarray:
    """Return a constant Q_ij field with principal axis along z (disk normal).
    Shape: (ny, nx, 3, 3)."""
    Q = np.zeros((ny, nx, 3, 3), dtype=float)
    # Set Qzz positive and trace-free: diag(-1/3, -1/3, 2/3)
    Q[..., 0, 0] = -1/3
    Q[..., 1, 1] = -1/3
    Q[..., 2, 2] = 2/3
    return Q

def director_n_from_Q(Q: np.ndarray) -> np.ndarray:
    """Pick the max-eigenvector per pixel; here, z-hat for the scaffold."""
    ny, nx = Q.shape[:2]
    n = np.zeros((ny, nx, 3), dtype=float)
    n[..., 2] = 1.0
    return n

