from __future__ import annotations
import numpy as np


def transmissivity_weight_from_ne(ne: np.ndarray, spacing: tuple[float,float,float], ref_scale: float = 1.0) -> np.ndarray:
    """Compute a simple line-of-sight transmissivity weight W in [0,1].

    Placeholder: returns ones (W≈1), preserving interface for future n_e-based models.
    """
    return np.ones_like(ne, dtype=float)

