from __future__ import annotations
import numpy as np
from .sph import lm_index
from .structure_tensor import structure_tensor, anisotropy_strengths


def construct_ahat_coeffs(
    rho: np.ndarray,
    spacing: tuple[float,float,float],
    lmax: int = 2,
    method: str = 'structure_tensor',
    smooth_sigma: float | None = None,
) -> np.ndarray:
    """Construct a_lm(y) coefficients per voxel.

    Returns array of shape (nz, ny, nx, L) with L=(lmax+1)^2.
    Enforces l=0 component to 0 (we use Â = 1 + Σ_{l>=2} ...); a_{lm}=0 for l=1 by definition.
    For now, provides a stub that zeros all a_{lm} for l>=2, i.e., isotropic baseline.

    method='structure_tensor' reserved for future: estimate principal axes e_p and anisotropy strengths b_p
    from gradients/Hessian of ρ.
    """
    nz, ny, nx = rho.shape
    L = (lmax + 1) ** 2
    coeffs = np.zeros((nz, ny, nx, L), dtype=np.float32)
    if method == 'structure_tensor' and lmax >= 2:
        evals, evecs = structure_tensor(rho, spacing=spacing)
        b = anisotropy_strengths(evals)
        # Map anisotropy to quadrupole amplitude α times (e_z^2 − 1/3 I) in local frame.
        # Simple heuristic: α ∝ max(|b_p|), sign from principal direction.
        alpha = np.max(np.abs(b), axis=-1)
        # Assign a pure l=2, m=0 in the local principal frame; leave rotation TODO.
        # In global frame this is not strictly correct; acts as placeholder.
        idx_l2m0 = 2*2 + (0 + 2)
        coeffs[..., idx_l2m0] = alpha.astype(np.float32)
    # Optional smoothing of coefficients to control high‑k behavior
    if smooth_sigma is not None and smooth_sigma > 0:
        try:
            from scipy.ndimage import gaussian_filter
            for idx in range(L):
                coeffs[..., idx] = gaussian_filter(coeffs[..., idx], smooth_sigma)
        except Exception:
            pass
    return coeffs
