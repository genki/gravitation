#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULW 放射×記録のサムルール確認デモ:
  C = (1/4π) ∫ φ_emit(ω) σ_M(ω) dω  ≟  G/c

サンプルの φ_emit, σ_M を用いて数値積分し、G/c と比較します。
"""
from __future__ import annotations

import numpy as np

G = 6.67430e-11  # m^3 kg^-1 s^-2
c = 2.99792458e8  # m s^-1


def phi_emit(omega: np.ndarray) -> np.ndarray:
    """単位質量あたりの放射数率 [s^-1 Hz^-1 kg^-1].
    サンプル: 低周波寄りのブロードロールオフ φ0 * (1 + (ω/ω0)^p)^-1
    """
    phi0 = 3e-16  # s^-1 kg^-1 の目安（全積分で ~phi0）
    w0 = 1.0  # Hz
    p = 2.0
    return (phi0 / np.log(10)) * (1.0 / (1.0 + (omega / w0) ** p)) * (1.0 / (omega + 1e-30))


def sigma_M(omega: np.ndarray) -> np.ndarray:
    """単位質量あたりの実効記録断面積 [m^2 kg^-1].
    サンプル: 低周波で飽和し高周波で減衰 Σ0 / (1 + (ω/ωc)^q)
    """
    Sigma0 = 1e-2  # m^2 kg^-1 の目安
    wc = 0.5  # Hz
    q = 2.0
    return Sigma0 / (1.0 + (omega / wc) ** q)


def integrate_trapz(f: np.ndarray, x: np.ndarray) -> float:
    return float(np.trapz(f, x))


def main() -> None:
    # 対数周波数グリッド
    w = np.logspace(-6, 2, 10000)  # 1 µHz .. 100 Hz
    val = integrate_trapz(phi_emit(w) * sigma_M(w), w)
    C = val / (4.0 * np.pi)
    target = G / c
    rel = abs(C - target) / target
    print(f"C(num)   = {C:.6e} m^2/(s·kg)")
    print(f"G/c      = {target:.6e} m^2/(s·kg)")
    print(f"rel.err  = {rel:.3e}")
    print("(サンプル形状はスケール感のみ。φ_emit, σ_M を実測に置換可)")


if __name__ == "__main__":
    main()

