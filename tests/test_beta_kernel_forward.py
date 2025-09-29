import numpy as np
from src.models.fdbl import irradiance_log_bias

def make_gaussian(nx=128, ny=128, pix=0.2, sigma_kpc=2.0):
    y = (np.arange(ny) - (ny - 1)/2.0) * pix
    x = (np.arange(nx) - (nx - 1)/2.0) * pix
    yy, xx = np.meshgrid(y, x, indexing='ij')
    j = np.exp(-0.5 * (xx**2 + yy**2) / (sigma_kpc**2))
    return j

def forward_component(gx, gy, angle_deg):
    th = np.deg2rad(angle_deg); cu, su = np.cos(th), np.sin(th)
    return (gx * cu + gy * su).mean()

def test_beta_angle_kernel_increases_forward_component():
    j = make_gaussian()
    pix = 0.2
    # baseline (Lambert proxy)
    gx0, gy0 = irradiance_log_bias(j, pix_kpc=pix, strength=1.0, eps_kpc=0.5, pad_factor=1, beta_forward=0.0, forward_angle_deg=0.0)
    f0 = forward_component(gx0, gy0, 0.0)
    # forwardized
    gx1, gy1 = irradiance_log_bias(j, pix_kpc=pix, strength=1.0, eps_kpc=0.5, pad_factor=1, beta_forward=0.6, forward_angle_deg=0.0)
    f1 = forward_component(gx1, gy1, 0.0)
    assert f1 > f0
