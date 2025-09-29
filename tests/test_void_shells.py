from __future__ import annotations

import numpy as np
from src.toy.void_shells import accel_from_shell


def rel_err(x, y):
    return np.max(np.abs(x - y) / np.maximum(np.abs(y), 1e-12))


def test_shell_outside_inside_behavior():
    R = 5.0
    r_out = np.linspace(R*1.2, R*3.0, 25)
    r_in = np.linspace(0.5, R*0.9, 20)
    a_out = accel_from_shell(r_out, R_shell=R, n_pts=6000, mass_eff=1.0)
    a_in = accel_from_shell(r_in, R_shell=R, n_pts=6000, mass_eff=1.0)
    # Outside ~ 1/r^2 with G*M=1
    target = 1.0 / (r_out ** 2)
    assert rel_err(a_out, target) < 0.03  # ±3%
    # Inside ~ 0
    assert np.max(np.abs(a_in)) < 1e-2

