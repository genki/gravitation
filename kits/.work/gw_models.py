
from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class PolarizationStackModel:
    """Heuristic model for estimating uncertainty on a small non-TT fraction f_nonTT
    from a network of detectors and a set of events.
    sigma_f ≈ 1 / (Gpol * sqrt(sum SNR_i^2)).
    Gpol is a geometry lever (<=1), encapsulating network angular diversity, calibration, etc.
    """
    Gpol: float = 0.3  # conservative geometry lever (0< Gpol ≤ 1)
    def sigma_f(self, snr_list) -> float:
        s = np.sqrt(np.sum(np.asarray(snr_list, dtype=float)**2))
        if s <= 0: 
            return np.inf
        return 1.0 / (self.Gpol * s)
    def required_events(self, target_sigma: float, snr_per_event: float) -> int:
        if self.Gpol <= 0 or snr_per_event <= 0: 
            return 10**9
        n = (1.0 / (self.Gpol * target_sigma * snr_per_event))**2
        return int(np.ceil(n))

@dataclass
class MemoryStackModel:
    """Simple stacking SNR model for memory detection.
    We treat per-event 'memory SNR' m_i as an input (from a waveform pipeline).
    Stacked SNR = sqrt(sum m_i^2).
    """
    rho_thresh: float = 5.0
    def stacked_snr(self, m_list) -> float:
        return float(np.sqrt(np.sum(np.asarray(m_list, dtype=float)**2)))
    def required_events(self, m_single: float) -> int:
        if m_single <= 0: 
            return 10**9
        n = (self.rho_thresh / m_single)**2
        return int(np.ceil(n))
