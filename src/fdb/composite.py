from __future__ import annotations
import numpy as np
from typing import Tuple, Dict, Any
from .boundary import build_rho_eff_boundary


def build_layers(
    rho_star: np.ndarray,
    rho_gas: np.ndarray,
    proxy_ne_like: np.ndarray,
    spacing: Tuple[float,float,float],
    gas_scale: float,
    alpha_esc: float,
    ell_star: float,
    omega_star: float,
    smooth_sigma: float | None = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Build isotropic and surface-additive layers and the total effective density.

    Returns (rho_iso, S, rho_eff, meta)
    - rho_iso = rho_star + gas_scale * rho_gas (GR等価側; 減衰無し)
    - S = thin-layer source built from proxy (direction-averaged magnitude)
    - rho_eff = rho_iso + alpha_esc * S
    """
    rho_iso = (rho_star.astype(float) + float(gas_scale) * rho_gas.astype(float))
    S_only, meta = build_rho_eff_boundary(
        rho=np.zeros_like(rho_iso),  # boundary module adds only S term when alpha_esc=1
        proxy=proxy_ne_like,
        spacing=spacing,
        omega_star=omega_star,
        alpha_esc=1.0,
        ell_star=ell_star,
        smooth_sigma=smooth_sigma,
    )
    # S_only here equals S (since base rho was zeros) due to current implementation
    S = S_only
    rho_eff = rho_iso + float(alpha_esc) * S
    meta.update({'gas_scale': float(gas_scale)})
    return rho_iso, S, rho_eff, meta

