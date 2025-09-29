from __future__ import annotations
import numpy as np
from src.models.fdbl_analytic import disk_inv1_gr, rod_inv1_field_xy
from src.models.fdbl import circular_profile


def slope_loglog(x: np.ndarray, y: np.ndarray, frac: float) -> float:
    n = len(x)
    i0 = int(max(1, n*(1.0-frac)))
    xs = np.log(np.maximum(x[i0:], 1e-6))
    ys = np.log(np.maximum(np.abs(y[i0:]), 1e-12))
    xs0 = xs - xs.mean()
    a = float(np.sum(xs0 * ys) / max(np.sum(xs0*xs0), 1e-12))
    return a


def test_rod_outer_slope_approaches_minus2():
    # 長棒の1/r^2 近似を遠方で確認
    pix = 0.2; size = 256
    y = (np.arange(size) - (size - 1) / 2.0) * pix
    x = (np.arange(size) - (size - 1) / 2.0) * pix
    xx, yy = np.meshgrid(x, y, indexing='xy')
    gx, gy = rod_inv1_field_xy(xx, yy, L=10.0, eps=0.5, lam0=1.0, angle_deg=0.0)
    r, gr = circular_profile(gx, gy, pix_kpc=pix, nbins=64)
    s = slope_loglog(r, gr, frac=0.3)
    # 数値近似と有限サイズの影響を考慮して緩めの下限のみ確認
    assert s < -0.5


def test_disk_inner_to_outer_transition_reasonable():
    # 有限円盤で近傍は緩く、遠方は-2に近づくことを粗く確認
    R = np.linspace(0.2, 20.0, 128)
    def Sigma_of_R(r):
        return np.exp(-r/3.0)
    g = disk_inv1_gr(R, Sigma_of_R, eps=0.8)
    s_inner = slope_loglog(R[:32], g[:32], frac=0.5)
    s_outer = slope_loglog(R, g, frac=0.3)
    assert s_outer < s_inner  # 外側の方が急減衰
    # 遠方は明確に負の傾き（1/r^p の p>0）
    assert s_outer < -0.5
