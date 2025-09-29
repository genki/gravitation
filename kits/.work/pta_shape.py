
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from common import hd_curve, flat_scalar_correlation, rms

@dataclass
class PTACorrelationShapeTest:
    """Compare a mixed correlation C(θ) = (1 - f) * C_TT(θ) + f * C_alt(θ)
    with the pure TT Hellings–Downs shape. Return RMS shape deviation and a crude
    estimate of pairs needed given per-pair correlation error sigma_pair.
    """
    f_nonTT: float = 0.05  # 5% admixture of non-TT mode (phenomenological)
    def rms_shape_deviation(self, theta_rad: np.ndarray, alt='flat') -> float:
        C_tt = hd_curve(theta_rad)
        if alt == 'flat':
            C_alt = flat_scalar_correlation(theta_rad)
        else:
            # custom alt; for extensibility one could pass a callable; here we keep 'flat'
            C_alt = flat_scalar_correlation(theta_rad)
        C_mix = (1.0 - self.f_nonTT) * C_tt + self.f_nonTT * C_alt
        return rms(C_mix - C_tt)
    def required_pairs(self, rms_dev: float, sigma_pair: float) -> int:
        """Crude requirement: RMS deviation exceeds noise/√Npairs by ~1σ."""
        if sigma_pair <= 0 or rms_dev <= 0:
            return 10**9
        n = (sigma_pair / rms_dev)**2
        return int(np.ceil(n))
