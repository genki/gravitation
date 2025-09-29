
from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class FRBAchromaticBlurModel:
    """Model extra achromatic broadening τ_achr from FDB along a lensing path.
    τ_achr = tau0 * Kappa_eff, where Kappa_eff is an effective (dimensionless) surface-density proxy
    such as Σ/Σ_crit integrated along the path. This is a *phenomenological* handle.
    """
    tau0_us: float = 50.0  # normalization in microseconds per unit Kappa_eff
    def tau_achr_us(self, kappa_eff: np.ndarray) -> np.ndarray:
        return self.tau0_us * np.asarray(kappa_eff, dtype=float)
    def detectability(self, tau_us: float, time_resolution_us: float, snr_pulse: float) -> float:
        """Return a naive Z-score: tau / (time_resolution / sqrt(SNR))."""
        if time_resolution_us <= 0 or snr_pulse <= 0:
            return 0.0
        sigma_eff = time_resolution_us / np.sqrt(snr_pulse)
        return tau_us / sigma_eff
