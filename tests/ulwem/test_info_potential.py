import numpy as np

from src.ulwem import (
    G,
    C,
    phi_point_mass,
    accel_point_mass,
    deflection_point_mass,
    v2_exponential_disk,
)


def test_point_mass_accel_matches_minus_grad_phi():
    M = 1.0e30  # kg
    # sample points in 3D
    pts = np.array(
        [
            [1.0e9, 0.0, 0.0],
            [0.0, -2.0e9, 0.0],
            [3.0e9, 4.0e9, 0.0],
        ]
    )
    r = np.linalg.norm(pts, axis=1)
    # analytic a = -GM r_hat / r^2
    a_ref = -(G * M) * pts / (r[:, None] ** 3)
    a = accel_point_mass(M, pts)
    assert np.allclose(a, a_ref, rtol=1e-12, atol=0.0)


def test_point_mass_deflection_formula():
    M = 5.0e30  # kg
    b = np.array([1.0e11, 2.0e11])
    alpha = deflection_point_mass(M, b)
    alpha_ref = 4 * G * M / (b * C * C)
    assert np.allclose(alpha, alpha_ref, rtol=1e-15, atol=0.0)


def test_exponential_disk_v2_smoke():
    Sigma0 = 100.0  # kg m^-2 (arbitrary)
    Rd = 1.0e20  # m
    R = np.linspace(1e18, 5e20, 16)
    v2 = v2_exponential_disk(R, Sigma0, Rd)
    assert np.all(np.isfinite(v2))
    assert (v2 > 0).any()

