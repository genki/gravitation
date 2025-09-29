import numpy as np
from scripts.compare_fit_multi import compute_inv1_unit


def test_surface_mode_beta_forward_affects_profile():
    # synthetic radial grid and exponential SB profile
    R = np.linspace(0.2, 12.0, 180)
    SB = np.exp(-R / 3.0)
    pix = 0.2
    size = 128
    eps = 0.6

    g0 = compute_inv1_unit(
        'fft', R, SB, pix_kpc=pix, size=size, line_eps_kpc=eps,
        pad_factor=1, beta_forward=0.0, forward_angle_deg=0.0
    )
    g1 = compute_inv1_unit(
        'fft', R, SB, pix_kpc=pix, size=size, line_eps_kpc=eps,
        pad_factor=1, beta_forward=0.7, forward_angle_deg=0.0
    )
    # compare_fit_multi の表層モード配線では radial_forwardize を適用する
    from src.fdb.angle_kernels import radial_forwardize
    g1 = radial_forwardize(R, g1, beta=0.7)

    # Compare outer-to-inner ratios: forwardization should relatively boost outer radii
    inner = np.nanmean(g0[(R >= 0.5) & (R <= 2.0)])
    outer = np.nanmean(g0[(R >= 8.0) & (R <= 11.0)])
    r0 = float(outer / max(inner, 1e-12))

    inner1 = np.nanmean(g1[(R >= 0.5) & (R <= 2.0)])
    outer1 = np.nanmean(g1[(R >= 8.0) & (R <= 11.0)])
    r1 = float(outer1 / max(inner1, 1e-12))

    assert r1 > r0
