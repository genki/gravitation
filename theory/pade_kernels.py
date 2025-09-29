from __future__ import annotations
"""Padé近似の雛形: 有限ディスク/ロッドの 1/r 核によるg_R(R)を近似。

ここでは、厳密数値（src/models/fdbl_analytic.pyの ring/rod 積分）との相対誤差を検証する枠組みのみ提供し、
Padé係数は簡易（経験的）な初期値を置いてある。係数は scripts/reports/geom_kernel_pade_demo.py で
非線形最小二乗により最適化可能。
"""
import numpy as np
from typing import Tuple, Callable
from src.models.fdbl_analytic import disk_inv1_gr


def pade_disk_gR(R: np.ndarray, a: float, eps: float) -> np.ndarray:
    """均一円盤半径aの近似 g_R(R)（Padé [2/2] の雛形）。
    形式: g ≈ R * (c0 + c1 x + c2 x^2) / (1 + d1 x + d2 x^2), x=R/a
    係数は初期値。scripts/reports/geom_kernel_pade_demo.py で最適化可能。
    """
    x = np.asarray(R, float) / max(a, 1e-12)
    c0, c1, c2 = 1.0, 0.1, -0.05
    d1, d2 = 0.7, 0.15
    num = c0 + c1 * x + c2 * x * x
    den = 1.0 + d1 * x + d2 * x * x
    return (x * num / np.maximum(den, 1e-12)) * (1.0 / max(a, 1e-12))


def disk_true_gR(R: np.ndarray, a: float, eps: float, Sigma0: float = 1.0) -> np.ndarray:
    def Sigma_of_R(rho: np.ndarray) -> np.ndarray:
        return np.where(rho <= a, Sigma0, 0.0)
    return disk_inv1_gr(R, Sigma_of_R, eps=eps)

