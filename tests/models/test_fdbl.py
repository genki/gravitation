import numpy as np
import numpy.testing as npt

from src.models.fdbl import (
    solve_phi_yukawa_2d,
    solve_phi_yukawa_aniso,
    solve_phi_yukawa_nonlinear,
    grad_from_phi,
    _gaussian_filter_fft,
    structure_boost,
    plane_bias_weight,
    bar_bias_weight,
    irradiance_bias,
    circular_profile,
    exponential_disk,
    gaussian_sources,
    vc_from_gr,
)


def test_grad_from_phi_quadratic():
    ny, nx = 64, 64
    pix = 0.5
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix
    yy, xx = np.meshgrid(y, x, indexing="ij")
    phi = xx * xx + yy * yy
    gx, gy = grad_from_phi(phi, pix)
    # central difference approximates 2x, 2y well in interior
    m = (np.abs(xx) < (x.max() * 0.8)) & (np.abs(yy) < (y.max() * 0.8))
    npt.assert_allclose(gx[m], 2.0 * xx[m], rtol=0.03, atol=0.03)
    npt.assert_allclose(gy[m], 2.0 * yy[m], rtol=0.03, atol=0.03)


def test_gaussian_filter_constant():
    img = np.full((32, 48), 3.14)
    out = _gaussian_filter_fft(img, 2.5)
    npt.assert_allclose(out, img, rtol=0, atol=1e-6)


def test_structure_boost_range_and_shape():
    rng = np.random.default_rng(0)
    j = rng.standard_normal((64, 64)).astype(float)
    F = structure_boost(j, 1.0, 3.0, alpha=0.7, pnorm=90.0)
    assert F.shape == j.shape
    assert np.nanmin(F) >= 1.0


def test_yukawa_solves_and_grad_sign():
    ny, nx = 64, 64
    pix = 0.2
    j = np.zeros((ny, nx))
    j[ny // 2, nx // 2] = 1.0
    phi = solve_phi_yukawa_2d(j, pix, lam_kpc=2.0, beta=1.0)
    gx, gy = grad_from_phi(phi, pix)
    # central peak, gradient points outward. Check away from center.
    assert np.nanmax(phi) == phi[ny // 2, nx // 2]
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix
    left = gx[:, x < (-2 * pix)]
    right = gx[:, x > (2 * pix)]
    assert np.nanmean(left) > 0.0
    assert np.nanmean(right) < 0.0


def test_aniso_and_nonlinear_variants_return_finite():
    j = exponential_disk(64, 64, pix_kpc=0.2, i0=1.0, r_d_kpc=1.5)
    phi_a = solve_phi_yukawa_aniso(j, 0.2, 3.0, 1.0, q_axis=0.7,
                                   angle_deg=30.0)
    phi_n = solve_phi_yukawa_nonlinear(j, 0.2, 3.0, 1.0,
                                       gamma=0.4, power_q=1.0, n_iter=2)
    assert np.isfinite(phi_a).all()
    assert np.isfinite(phi_n).all()


def test_weight_fields_shapes_and_bounds():
    nx, ny = 50, 40
    Wp = plane_bias_weight(nx, ny, 0.2, alpha=0.5, r0_kpc=1.0)
    Wb = bar_bias_weight(nx, ny, 0.2, angle_deg=25.0, width_kpc=0.8,
                         alpha=0.6, r0_kpc=1.0)
    assert Wp.shape == (ny, nx)
    assert Wb.shape == (ny, nx)
    assert np.nanmin(Wp) >= 1.0
    assert np.nanmin(Wb) >= 1.0


def test_irradiance_bias_zero_strength():
    j = np.ones((32, 32))
    gx, gy = irradiance_bias(j, 0.5, strength=0.0)
    npt.assert_allclose(gx, 0.0)
    npt.assert_allclose(gy, 0.0)


def test_circular_profile_and_vc():
    ny, nx = 64, 64
    pix = 0.5
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix
    yy, xx = np.meshgrid(y, x, indexing="ij")
    gx = 0.1 * xx
    gy = 0.1 * yy
    r, gr = circular_profile(gx, gy, pix, nbins=32)
    # For linear field, g_r ≈ 0.1 r (averaged), vc ≈ sqrt(r*0.1 r)=0.316 r
    vc = vc_from_gr(gr, r)
    assert len(r) == len(gr) == len(vc)
    assert np.nanmean(vc[1:] / r[1:]) > 0.25
    assert np.nanmean(vc[1:] / r[1:]) < 0.4


def test_source_generators_shapes():
    j1 = exponential_disk(33, 31, 0.3, 2.0, 1.2)
    assert j1.shape == (31, 33)
    j2 = gaussian_sources(20, 10, 0.5, [(0.0, 0.0), (1.0, -1.0)], 0.8)
    assert j2.shape == (10, 20)
