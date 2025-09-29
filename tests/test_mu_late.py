from __future__ import annotations

import numpy as np
import pytest
from src.cosmo.mu_late import mu_late, eps_of_a, shape_S_of_k


def test_eps_of_a_monotonic():
    a = np.linspace(0.01, 1.0, 200)
    e = eps_of_a(a, eps_max=0.12, a_on=0.05, da=0.02)
    assert np.all(np.diff(e) >= -1e-8)
    assert e[0] < e[-1]
    assert e[-1] == pytest.approx(0.12, rel=1e-2)


def test_shape_S_limits():
    k = np.geomspace(1e-4, 1e2, 400)
    s = shape_S_of_k(k, k_c=0.2)
    assert 0.0 <= np.min(s) <= 1.0
    assert 0.0 <= np.max(s) <= 1.0
    assert s[0] < 0.01  # at k<<k_c
    assert s[-1] > 0.99  # at k>>k_c


def test_mu_late_broadcast_and_bounds():
    a = np.array([0.02, 0.05, 0.1, 0.5])
    k = np.array([1e-3, 0.1, 1.0])
    MU = mu_late(a[:, None], k[None, :], eps_max=0.1, a_on=0.05, da=0.02, k_c=0.2)
    assert MU.shape == (len(a), len(k))
    assert np.all(MU >= 1.0)
    # After turn-on and at large k, should exceed 1 noticeably
    assert MU[-1, -1] > 1.02
