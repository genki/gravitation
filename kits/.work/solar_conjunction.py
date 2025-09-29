
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from common import R_sun

@dataclass
class AchromaticShapiroResidualModel:
    """Model residual RMS as sigma_t(b) = sigma0 ⊕ (xi / b^2) in quadrature.
    Here '⊕' means added in quadrature; b is impact parameter (m).
    sigma0 captures instrument + plasma-corrected floor (achromatic), xi is the FDB-induced strength.
    """
    sigma0_ps: float = 5.0   # ps baseline floor after two-color plasma removal
    xi_ps_Rsun2: float = 0.0 # parameter in [ps * R_sun^2]; convert internally to SI
    def sigma_ps(self, b_m: np.ndarray) -> np.ndarray:
        b = np.asarray(b_m, dtype=float)
        term = self.xi_ps_Rsun2 / ((b / R_sun)**2)
        return np.sqrt(self.sigma0_ps**2 + term**2)
