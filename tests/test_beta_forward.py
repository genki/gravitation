import numpy as np
from src.fdb.angle_kernels import radial_forwardize

def linfit(x, y):
    x = np.asarray(x); y = np.asarray(y)
    x = x - x.mean()
    a = float((x*y).sum() / (x*x).sum())
    b = float(y.mean())
    return a, b

def test_radial_forwardize_increases_slope():
    R = np.linspace(0.1, 10.0, 200)
    g = 1.0 / (R + 0.5)  # decaying profile
    a0, _ = linfit(R, g)
    g_fwd = radial_forwardize(R, g, beta=0.6)
    a1, _ = linfit(R, g_fwd)
    # Forwardization should make the profile less steeply negative (or positive if boosted enough)
    # i.e., slope increases numerically
    assert a1 > a0
