from __future__ import annotations

import numpy as np
from src.astro.uvlf_boost import uvlf_multiplier


def test_uvlf_multiplier_monotonic_in_D():
    nu = 4.0
    r = np.array([1.00, 1.05, 1.10, 1.15])
    R = uvlf_multiplier(nu, r)
    assert np.all(np.diff(R) > 0)
    assert R[0] == 1.0
    # sanity: ~4× at ν=4 and D'/D≈1.10
    assert R[2] > 3.0

