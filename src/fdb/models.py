from __future__ import annotations

import numpy as np


def gr_baryon_velocity(
    r_kpc: np.ndarray,
    v_gas: np.ndarray,
    v_disk: np.ndarray,
    v_bul: np.ndarray,
    ml_disk: float = 0.5,
    ml_bul: float = 0.7,
) -> np.ndarray:
    """GR(no DM)におけるバリオン寄与の円運動速度[km/s]。

    SPARCの慣例に合わせ、星のM/Lをスケール因子として
    速度二乗へ線形に掛ける（質量比例→寄与はV^2に線形）。
    """
    v2 = (v_gas ** 2.0) + (ml_disk * (v_disk ** 2.0))
    v2 += (ml_bul * (v_bul ** 2.0))
    return np.sqrt(np.clip(v2, 0.0, None))


def fdb3_velocity(
    r_kpc: np.ndarray,
    v_gas: np.ndarray,
    v_disk: np.ndarray,
    v_bul: np.ndarray,
    a: float,
    b: float,
    c: float,
    ml_disk: float = 0.5,
    ml_bul: float = 0.7,
) -> np.ndarray:
    """FDB3（Future Decoherence Bias; 3-parameter）の予測円運動速度[km/s]。

    g = g_GR + a * (1 - exp(-r/b))**c を円運動に対応付ける。
    g = V^2 / r より、
    V^2 = V_baryon^2 + r * a * (1 - exp(-r/b))**c

    単位整合: r[kpc], a は [km^2 s^-2 kpc^-1] と解釈。
    """
    v_gr = gr_baryon_velocity(r_kpc, v_gas, v_disk, v_bul,
                              ml_disk, ml_bul)
    kern = (1.0 - np.exp(-np.clip(r_kpc / max(b, 1e-6), 0.0, None))) ** c
    v2 = (v_gr ** 2.0) + np.clip(r_kpc, 0.0, None) * a * kern
    return np.sqrt(np.clip(v2, 0.0, None))
