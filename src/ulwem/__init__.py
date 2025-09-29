"""ULW-EM: Information-potential (Doob h-transform) utilities.

This package implements the updated "future-fixation bias" formulation:
- U_info = kappa * log h, with weak-field normalization U_info = m * Phi_eff
- Point-mass helpers and lensing deflection for validation tests
- Thin-disk rotation curve (Freeman) as a smoke test
"""

from .info_potential import (
    G,
    C,
    phi_point_mass,
    accel_point_mass,
    u_info_mass,
    u_info_photon,
    deflection_point_mass,
    v2_exponential_disk,
)

__all__ = [
    "G",
    "C",
    "phi_point_mass",
    "accel_point_mass",
    "u_info_mass",
    "u_info_photon",
    "deflection_point_mass",
    "v2_exponential_disk",
]

