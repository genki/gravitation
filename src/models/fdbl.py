"""
FDB = Future Decoherence Bias（ULW-EM 起源の見かけの加速度/引力）
最小実装: 2D Yukawa 有効場ソルバー

方程式:
  (∇^2 - λ^{-2}) φ = β j_EM
  g_ULW = -η ∇φ

実装メモ:
- 2D平面でFFTにより φ を解く (k空間で除算)
- 円対称でなくても動作。円筒平均で v_c(R) を推定可能。

行幅80桁以内を心がける。
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def _pad_for_fft(img: NDArray[np.floating], pad_factor: int) -> NDArray[np.floating]:
    if pad_factor <= 1:
        return img
    ny, nx = img.shape
    py, px = int(ny * pad_factor), int(nx * pad_factor)
    out = np.zeros((py, px), dtype=img.dtype)
    sy, sx = (py - ny) // 2, (px - nx) // 2
    out[sy:sy + ny, sx:sx + nx] = img
    return out


def _crop_center(img: NDArray[np.floating], shape: tuple[int, int]) -> NDArray[np.floating]:
    ny, nx = shape
    py, px = img.shape
    sy, sx = (py - ny) // 2, (px - nx) // 2
    return img[sy:sy + ny, sx:sx + nx]


def solve_phi_yukawa_2d(
    j_em: NDArray[np.floating],
    pix_kpc: float,
    lam_kpc: float,
    beta: float,
    pad_factor: int = 1,
) -> NDArray[np.floating]:
    """2D Yukawa 方程式を FFT で解き φ を返す。

    j_em: 2D 配列 (任意単位の放射源強度)
    pix_kpc: 1ピクセルの物理スケール[kpc]
    lam_kpc: 相関長 λ[kpc]
    beta: 源→ポテンシャルの結合係数
    """
    j_pad = _pad_for_fft(j_em, pad_factor)
    ny, nx = j_pad.shape
    ky = np.fft.fftfreq(ny, d=pix_kpc) * 2.0 * np.pi
    kx = np.fft.fftfreq(nx, d=pix_kpc) * 2.0 * np.pi
    kyy, kxx = np.meshgrid(ky, kx, indexing="ij")
    k2 = kxx * kxx + kyy * kyy
    j_k = np.fft.rfftn(j_pad)
    # rFFT の波数は x: rfftfreq 相当、ここでは kxx を再構成する
    kx_r = np.fft.rfftfreq(nx, d=pix_kpc) * 2.0 * np.pi
    kyy_r, kxx_r = np.meshgrid(ky, kx_r, indexing="ij")
    k2_r = kxx_r * kxx_r + kyy_r * kyy_r
    denom = k2_r + (1.0 / (lam_kpc * lam_kpc))
    # k=0 のとき denom>0 なのでゼロ割なし
    phi_k = beta * j_k / denom
    phi_pad = np.fft.irfftn(phi_k, s=(ny, nx))
    if pad_factor > 1:
        phi = _crop_center(phi_pad, j_em.shape)
    else:
        phi = phi_pad
    return phi


def solve_phi_yukawa_aniso(
    j_em: NDArray[np.floating],
    pix_kpc: float,
    lam_kpc: float,
    beta: float,
    q_axis: float = 1.0,
    angle_deg: float = 0.0,
    pad_factor: int = 1,
) -> NDArray[np.floating]:
    """異方Yukawa: 回転・軸比q_axis(<=1で扁平)の有効核を用いる。"""
    j_pad = _pad_for_fft(j_em, pad_factor)
    ny, nx = j_pad.shape
    ky = np.fft.fftfreq(ny, d=pix_kpc) * 2.0 * np.pi
    kx = np.fft.rfftfreq(nx, d=pix_kpc) * 2.0 * np.pi
    kyy, kxx = np.meshgrid(ky, kx, indexing="ij")
    th = np.deg2rad(angle_deg)
    c, s = np.cos(th), np.sin(th)
    kx_p = kxx * c + kyy * s
    ky_p = -kxx * s + kyy * c
    q = max(q_axis, 1e-3)
    k2_r = kx_p * kx_p + (ky_p / q) * (ky_p / q)
    denom = k2_r + (1.0 / (lam_kpc * lam_kpc))
    j_k = np.fft.rfftn(j_pad)
    phi_k = beta * j_k / denom
    phi_pad = np.fft.irfftn(phi_k, s=(ny, nx))
    phi = _crop_center(phi_pad, j_em.shape) if pad_factor > 1 else phi_pad
    return phi


def solve_phi_yukawa_nonlinear(
    j_em: NDArray[np.floating],
    pix_kpc: float,
    lam_kpc: float,
    beta: float,
    gamma: float = 0.5,
    power_q: float = 1.0,
    n_iter: int = 3,
    pad_factor: int = 1,
) -> NDArray[np.floating]:
    """近似的な非線形源カップリング: j_eff = j*(1+gamma|∇φ|^2)^q。

    固定点反復でφを更新（各反復は線形YukawaをFFTで解く）。
    """
    phi = solve_phi_yukawa_2d(j_em, pix_kpc, lam_kpc, beta, pad_factor=pad_factor)
    for _ in range(max(n_iter, 0)):
        dpx, dpy = grad_from_phi(phi, pix_kpc)
        grad2 = dpx * dpx + dpy * dpy
        boost = np.power(1.0 + max(gamma, 0.0) * grad2, power_q)
        j_eff = j_em * boost
        phi = solve_phi_yukawa_2d(j_eff, pix_kpc, lam_kpc, beta, pad_factor=pad_factor)
    return phi


def grad_from_phi(
    phi: NDArray[np.floating], pix_kpc: float
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """中心差分で ∇φ を計算する。"""
    d = pix_kpc
    dphi_dx = (np.roll(phi, -1, axis=1) - np.roll(phi, 1, axis=1)) / (2.0 * d)
    dphi_dy = (np.roll(phi, -1, axis=0) - np.roll(phi, 1, axis=0)) / (2.0 * d)
    return dphi_dx, dphi_dy


def _gaussian_filter_fft(
    img: NDArray[np.floating], sigma_pix: float
) -> NDArray[np.floating]:
    """FFTでガウシアン平滑化を行う。"""
    if sigma_pix <= 0:
        return img.copy()
    ny, nx = img.shape
    ky = np.fft.fftfreq(ny, d=1.0) * 2.0 * np.pi
    kx = np.fft.rfftfreq(nx, d=1.0) * 2.0 * np.pi
    kyy, kxx = np.meshgrid(ky, kx, indexing="ij")
    k2 = kxx * kxx + kyy * kyy
    # 注意: 物理ピクセルスケールはsigma_pixに反映済
    H = np.exp(-0.5 * (sigma_pix * sigma_pix) * k2)
    Ik = np.fft.rfftn(img)
    Ok = Ik * H
    out = np.fft.irfftn(Ok, s=img.shape)
    return out


def structure_boost(
    j_em: NDArray[np.floating],
    sigma1_pix: float,
    sigma2_pix: float,
    alpha: float = 0.5,
    pnorm: float = 95.0,
) -> NDArray[np.floating]:
    """構造強度からブースト係数 F=1+alpha*B を計算する。

    DoG(差分ガウシアン)の絶対値を正規化(最大1)してBとする。
    """
    if alpha <= 0:
        return np.ones_like(j_em)
    s1 = max(float(sigma1_pix), 0.0)
    s2 = max(float(sigma2_pix), s1 + 1e-6)
    lo = _gaussian_filter_fft(j_em, s2)
    hi = _gaussian_filter_fft(j_em, s1)
    band = np.abs(hi - lo)
    # 外れに頑健な正規化: 指定パーセンタイルを使用
    m = float(np.nanpercentile(band, pnorm)) or float(np.nanmax(band)) or 1.0
    b = band / m
    return 1.0 + alpha * b


def plane_bias_weight(
    nx: int,
    ny: int,
    pix_kpc: float,
    alpha: float = 0.0,
    r0_kpc: float = 1.0,
) -> NDArray[np.floating]:
    """円盤面上の中心指向1/r風ブースト: W = 1 + alpha * r0/(r+r0).

    2D平面近似。rは画像中心からの半径。
    """
    if alpha <= 0:
        return np.ones((ny, nx), dtype=float)
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    yy, xx = np.meshgrid(y, x, indexing="ij")
    r = np.hypot(xx, yy)
    w = 1.0 + alpha * (r0_kpc / (r + r0_kpc))
    return w


def bar_bias_weight(
    nx: int,
    ny: int,
    pix_kpc: float,
    angle_deg: float = 0.0,
    width_kpc: float = 1.0,
    alpha: float = 0.0,
    r0_kpc: float = 1.0,
) -> NDArray[np.floating]:
    """棒状構造の軸方向1/r風ブースト。

    - 角度angle_degの軸(u)方向に 1 + alpha * r0/(|u|+r0)
    - 垂直方向vにガウシアンで幅を限定(exp(-0.5*(v/σ)^2))
    """
    if alpha <= 0:
        return np.ones((ny, nx), dtype=float)
    th = np.deg2rad(angle_deg)
    c, s = np.cos(th), np.sin(th)
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    yy, xx = np.meshgrid(y, x, indexing="ij")
    u = xx * c + yy * s
    v = -xx * s + yy * c
    sig = max(width_kpc, 1e-6)
    core = (r0_kpc / (np.abs(u) + r0_kpc))
    trans = np.exp(-0.5 * (v / sig) ** 2)
    w = 1.0 + alpha * core * trans
    return w


def _kernel_irradiance_fft(
    ny: int,
    nx: int,
    pix_kpc: float,
    eps_kpc: float = 0.3,
    p: float = 2.0,
) -> NDArray[np.complexfloating]:
    """Irradiance近似の畳み込み核 K(r)≈1/(r^2+eps^2)^(p/2) のFFT。

    2D投影上で点球面光源の和を近似するため、1/r^p型核を用いる。
    p=2 で点逆二乗則、線積分で ≈1/r を再現。
    """
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    yy, xx = np.meshgrid(y, x, indexing="ij")
    r2 = xx * xx + yy * yy
    K = 1.0 / np.power(r2 + eps_kpc * eps_kpc, 0.5 * p)
    # 中心をゼロ周波数へシフトしてFFT
    K = np.fft.ifftshift(K)
    Kk = np.fft.rfftn(K)
    return Kk


def irradiance_bias(
    j_em: NDArray[np.floating],
    pix_kpc: float,
    strength: float = 0.0,
    eps_kpc: float = 0.3,
    p: float = 2.0,
    pad_factor: int = 1,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """照度 I = K * j を畳み込みで求め、g_add = -strength ∇I を返す。"""
    if strength <= 0.0:
        z = np.zeros_like(j_em)
        return z, z
    j_pad = _pad_for_fft(j_em, pad_factor)
    ny, nx = j_pad.shape
    Kk = _kernel_irradiance_fft(ny, nx, pix_kpc, eps_kpc=eps_kpc, p=p)
    Ik = np.fft.rfftn(j_pad) * Kk
    I_pad = np.fft.irfftn(Ik, s=(ny, nx))
    I = _crop_center(I_pad, j_em.shape) if pad_factor > 1 else I_pad
    dIx, dIy = grad_from_phi(I, pix_kpc)
    # Note: ∇I points inward (大域的に中心へ); 重力様加速度も内向きにしたいので正符号で加える
    gx = strength * dIx
    gy = strength * dIy
    return gx, gy


def _kernel_log_fft(
    ny: int,
    nx: int,
    pix_kpc: float,
    eps_kpc: float = 0.3,
) -> NDArray[np.complexfloating]:
    """2D対数核 K(r) = 0.5*ln(r^2+eps^2) のFFT。

    勾配は ~ r/(r^2+eps^2) となり、|∇K| ~ 1/r で外縁が1/r減衰の加速度を与える。
    """
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    yy, xx = np.meshgrid(y, x, indexing="ij")
    r2 = xx * xx + yy * yy
    K = 0.5 * np.log(r2 + eps_kpc * eps_kpc)
    # DC成分は∇で落ちるが、数値安定のため中心シフトのみ行う
    K = np.fft.ifftshift(K)
    return np.fft.rfftn(K)


def irradiance_log_bias(
    j_em: NDArray[np.floating],
    pix_kpc: float,
    strength: float = 0.0,
    eps_kpc: float = 0.3,
    pad_factor: int = 1,
    beta_forward: float = 0.0,
    forward_angle_deg: float = 0.0,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """対数核を用いた照度 I = (log核) * j に対し、g_add = -strength ∇I を返す。"""
    if strength <= 0.0:
        z = np.zeros_like(j_em)
        return z, z
    j_pad = _pad_for_fft(j_em, pad_factor)
    ny, nx = j_pad.shape
    Kk = _kernel_log_fft(ny, nx, pix_kpc, eps_kpc=eps_kpc)
    Ik = np.fft.rfftn(j_pad) * Kk
    I_pad = np.fft.irfftn(Ik, s=(ny, nx))
    I = _crop_center(I_pad, j_em.shape) if pad_factor > 1 else I_pad
    dIx, dIy = grad_from_phi(I, pix_kpc)
    gx = strength * dIx
    gy = strength * dIy
    # Optional forwardization by angular kernel proxy: w(θ;β) = (1+β cosθ)/(1+β/2)
    if beta_forward and beta_forward > 0.0:
        th = np.deg2rad(forward_angle_deg)
        cu, su = np.cos(th), np.sin(th)
        ny, nx = j_em.shape
        y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
        x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
        yy, xx = np.meshgrid(y, x, indexing="ij")
        r = np.hypot(xx, yy)
        with np.errstate(divide="ignore", invalid="ignore"):
            cos_theta = (xx * cu + yy * su) / np.where(r == 0.0, np.nan, r)
        beta = float(max(0.0, min(1.0, beta_forward)))
        w = (1.0 + beta * cos_theta) / (1.0 + 0.5 * beta)
        w = np.nan_to_num(w, nan=1.0, posinf=1.0, neginf=1.0)
        gx = gx * w
        gy = gy * w
    return gx, gy


def radial_outer_boost(
    nx: int,
    ny: int,
    pix_kpc: float,
    alpha: float = 0.0,
    r0_kpc: float = 1.0,
) -> NDArray[np.floating]:
    """外縁強調の半径重み: W = 1 + alpha * r/(r+r0)。"""
    if alpha <= 0.0:
        return np.ones((ny, nx), dtype=float)
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    yy, xx = np.meshgrid(y, x, indexing="ij")
    r = np.hypot(xx, yy)
    w = 1.0 + alpha * (r / (r + max(r0_kpc, 1e-6)))
    return w


def circular_profile(
    gx: NDArray[np.floating],
    gy: NDArray[np.floating],
    pix_kpc: float,
    nbins: int = 48,
) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
    """円筒平均で半径 R と g_R(R) を返す。

    g_R = (x gx + y gy)/R を各ピクセルで評価し、半径ビンで平均。
    """
    ny, nx = gx.shape
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    yy, xx = np.meshgrid(y, x, indexing="ij")
    r = np.hypot(xx, yy)
    with np.errstate(divide="ignore", invalid="ignore"):
        g_r = (xx * gx + yy * gy) / np.where(r == 0.0, np.nan, r)
    rmax = 0.5 * pix_kpc * min(nx, ny)
    edges = np.linspace(0.0, rmax, nbins + 1)
    rc = 0.5 * (edges[:-1] + edges[1:])
    gr = np.empty(nbins, dtype=float)
    for i in range(nbins):
        m = (r >= edges[i]) & (r < edges[i + 1])
        vals = g_r[m]
        gr[i] = np.nanmean(vals) if np.isfinite(vals).any() else np.nan
    return rc, gr


def exponential_disk(
    nx: int,
    ny: int,
    pix_kpc: float,
    i0: float,
    r_d_kpc: float,
) -> NDArray[np.floating]:
    """指数ディスクの放射源分布 j_EM を生成。j = i0 exp(-R/Rd)。"""
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    yy, xx = np.meshgrid(y, x, indexing="ij")
    r = np.hypot(xx, yy)
    j = i0 * np.exp(-r / r_d_kpc)
    return j


def gaussian_sources(
    nx: int,
    ny: int,
    pix_kpc: float,
    centers_kpc: list[tuple[float, float]],
    sigma_kpc: float,
    amp: float = 1.0,
) -> NDArray[np.floating]:
    """2Dガウス点源の重ね合わせで j_EM を生成する。

    centers_kpc: (x,y)[kpc] のリスト（中心原点は配列中心）
    sigma_kpc: ガウスのσ[kpc]
    amp: 各源の振幅（等しいと仮定）
    """
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    yy, xx = np.meshgrid(y, x, indexing="ij")
    j = np.zeros((ny, nx), dtype=float)
    s2 = 2.0 * sigma_kpc * sigma_kpc
    for cx, cy in centers_kpc:
        j += amp * np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / s2)
    return j


def vc_from_gr(gr: NDArray[np.floating], r: NDArray[np.floating]) -> NDArray[np.floating]:
    """円運動近似 v_c^2 = R g_R から v_c を計算。"""
    vc2 = r * gr
    vc = np.sqrt(np.clip(vc2, a_min=0.0, a_max=None))
    return vc
