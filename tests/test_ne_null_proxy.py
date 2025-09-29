import numpy as np
from src.models.fdbl import irradiance_log_bias

def make_anisotropic_map(nx=128, ny=128, pix=0.2):
    y = (np.arange(ny) - (ny - 1)/2.0) * pix
    x = (np.arange(nx) - (nx - 1)/2.0) * pix
    yy, xx = np.meshgrid(y, x, indexing='ij')
    # anisotropic ridge aligned with +x direction
    j = np.exp(-0.5 * (xx/2.0)**2) * np.exp(-0.5 * (yy/6.0)**2)
    return j

def forward_component(gx, gy, angle_deg):
    th = np.deg2rad(angle_deg); cu, su = np.cos(th), np.sin(th)
    return float((gx * cu + gy * su).mean())

def test_ne_shuffle_null_reduces_forward_signal():
    pix = 0.2
    j = make_anisotropic_map()
    gx, gy = irradiance_log_bias(j, pix_kpc=pix, strength=1.0, eps_kpc=0.5, pad_factor=1, beta_forward=0.6, forward_angle_deg=0.0)
    f_sig = abs(forward_component(gx, gy, 0.0))
    # shuffle (destroy spatial coherence)
    jr = j.ravel().copy(); np.random.default_rng(0).shuffle(jr); jr = jr.reshape(j.shape)
    gx_r, gy_r = irradiance_log_bias(jr, pix_kpc=pix, strength=1.0, eps_kpc=0.5, pad_factor=1, beta_forward=0.6, forward_angle_deg=0.0)
    f_shuf = abs(forward_component(gx_r, gy_r, 0.0))
    assert f_sig > f_shuf
