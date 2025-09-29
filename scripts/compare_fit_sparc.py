#!/usr/bin/env python3
"""
SPARC 1銀河に対し、
- GR(no DM): g = g_gas + mu * g_star を最小二乗でフィット
- ULW-EM(FDB Yukawa): g = g_gas + mu * g_star + g_ulw(lam,A)

を同時比較する。評価は加速度空間(g=V^2/R)で行い、muは解析的に
最小二乗解を求め、(lam,A)は粗グリッドで探索する。

出力: SVG図(観測V、GRフィット、ULWフィット)と適合度の表示。
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np

from scripts.fit_sparc_fdbl import (
    read_sparc_massmodels,
    make_axisymmetric_image,
)
from src.models.fdbl import (
    solve_phi_yukawa_2d,
    solve_phi_yukawa_aniso,
    solve_phi_yukawa_nonlinear,
    grad_from_phi,
    circular_profile,
    structure_boost,
    plane_bias_weight,
    bar_bias_weight,
    irradiance_bias,
    irradiance_log_bias,
    radial_outer_boost,
)
from src.models.fdbl_analytic import (
    disk_inv1_gr,
    rod_inv1_field_xy,
)


@dataclass
class Obs:
    R: np.ndarray
    V: np.ndarray
    eV: np.ndarray
    g: np.ndarray
    eg: np.ndarray


def to_accel(R: np.ndarray, V: np.ndarray, eV: np.ndarray) -> Obs:
    Rm = np.maximum(R, 1e-6)
    g = (V * V) / Rm
    eg = 2.0 * V * np.maximum(eV, 1e-6) / Rm
    return Obs(R=R, V=V, eV=eV, g=g, eg=eg)


def model_ulw_accel(
    R: np.ndarray,
    SBdisk: np.ndarray,
    lam_kpc: float,
    A: float,
    pix_kpc: float,
    size: int,
    boost: float = 0.0,
    boost_s1_kpc: float = 0.5,
    boost_s2_kpc: float = 1.5,
    plane_alpha: float = 0.0,
    plane_r0_kpc: float = 1.0,
    bar_alpha: float = 0.0,
    bar_angle_deg: float = 0.0,
    bar_width_kpc: float = 1.0,
    bar_r0_kpc: float = 1.0,
    irr_alpha: float = 0.0,
    irr_eps_kpc: float = 0.3,
    irr_p: float = 2.0,
    # advanced kernel options
    aniso_q: float = 1.0,
    aniso_angle: float = 0.0,
    nl_gamma: float = 0.0,
    nl_q: float = 1.0,
    nl_iter: int = 2,
    out_alpha: float = 0.0,
    out_r0_kpc: float = 1.0,
    pad_factor: int = 1,
    # optional second band (mixture)
    lam2_kpc: float | None = None,
    mix_w: float = 0.0,
) -> Tuple[np.ndarray, np.ndarray]:
    j = make_axisymmetric_image(R, SBdisk, pix_kpc, size)
    if nl_gamma > 0.0:
        phi = solve_phi_yukawa_nonlinear(
            j, pix_kpc, lam_kpc, beta=1.0, gamma=nl_gamma,
            power_q=nl_q, n_iter=nl_iter, pad_factor=pad_factor
        )
    elif aniso_q != 1.0:
        phi = solve_phi_yukawa_aniso(
            j, pix_kpc, lam_kpc, beta=1.0, q_axis=aniso_q,
            angle_deg=aniso_angle, pad_factor=pad_factor
        )
    else:
        phi = solve_phi_yukawa_2d(j, pix_kpc, lam_kpc, beta=1.0, pad_factor=pad_factor)
    dpx, dpy = grad_from_phi(phi, pix_kpc)
    gx = -A * dpx
    gy = -A * dpy
    # optional second band
    if lam2_kpc is not None and mix_w > 0.0:
        if nl_gamma > 0.0:
            phi2 = solve_phi_yukawa_nonlinear(
                j, pix_kpc, lam2_kpc, beta=1.0, gamma=nl_gamma,
                power_q=nl_q, n_iter=nl_iter, pad_factor=pad_factor
            )
        elif aniso_q != 1.0:
            phi2 = solve_phi_yukawa_aniso(
                j, pix_kpc, lam2_kpc, beta=1.0, q_axis=aniso_q,
                angle_deg=aniso_angle, pad_factor=pad_factor
            )
        else:
            phi2 = solve_phi_yukawa_2d(j, pix_kpc, lam2_kpc, beta=1.0, pad_factor=pad_factor)
        dpx2, dpy2 = grad_from_phi(phi2, pix_kpc)
        gx = (1.0 - mix_w) * gx + mix_w * (-A * dpx2)
        gy = (1.0 - mix_w) * gy + mix_w * (-A * dpy2)
    if boost > 0:
        s1_pix = boost_s1_kpc / pix_kpc
        s2_pix = boost_s2_kpc / pix_kpc
        F = structure_boost(j, s1_pix, s2_pix, alpha=boost)
        gx = gx * F
        gy = gy * F
    # Plane/Bar anisotropic boosts (multiplicative)
    if plane_alpha > 0.0:
        Wp = plane_bias_weight(j.shape[1], j.shape[0], pix_kpc,
                               alpha=plane_alpha, r0_kpc=plane_r0_kpc)
        gx *= Wp
        gy *= Wp
    if bar_alpha > 0.0:
        Wb = bar_bias_weight(j.shape[1], j.shape[0], pix_kpc,
                             angle_deg=bar_angle_deg,
                             width_kpc=bar_width_kpc,
                             alpha=bar_alpha, r0_kpc=bar_r0_kpc)
        gx *= Wb
        gy *= Wb
    if irr_alpha > 0.0:
        gx_add, gy_add = irradiance_bias(
            j, pix_kpc, strength=irr_alpha, eps_kpc=irr_eps_kpc, p=irr_p
        )
        gx += gx_add
        gy += gy_add
    if out_alpha > 0.0:
        Wo = radial_outer_boost(j.shape[1], j.shape[0], pix_kpc,
                                alpha=out_alpha, r0_kpc=out_r0_kpc)
        gx *= Wo
        gy *= Wo
    rgrid, gr = circular_profile(gx, gy, pix_kpc, nbins=64)
    # 外挿は端値で埋める（図描画のNaN回避）
    left_val = float(gr[0]) if np.isfinite(gr[0]) else 0.0
    right_val = float(gr[-1]) if np.isfinite(gr[-1]) else left_val
    g_ulw = np.interp(R, rgrid, gr, left=left_val, right=right_val)
    return g_ulw, rgrid


def fit_mu_linear(
    g_obs: np.ndarray,
    eg_obs: np.ndarray,
    g_gas: np.ndarray,
    g_star: np.ndarray,
    g_ulw: np.ndarray,
) -> float:
    # g_obs ≈ g_gas + mu*g_star + g_ulw → mu の重み付き最小二乗
    y = g_obs - g_gas - g_ulw
    x = g_star
    w = 1.0 / np.maximum(eg_obs, 1e-6)
    num = np.nansum(w * x * y)
    den = np.nansum(w * x * x)
    if den <= 0:
        return 0.0
    mu = num / den
    return float(max(mu, 0.0))


def chi2_accel(
    g_obs: np.ndarray,
    eg_obs: np.ndarray,
    g_model: np.ndarray,
) -> float:
    w = 1.0 / np.maximum(eg_obs, 1e-6)
    return float(np.nansum(((g_model - g_obs) * w) ** 2))


def fit_mu_linear_w(
    g_obs: np.ndarray,
    eg_obs: np.ndarray,
    g_gas: np.ndarray,
    g_star: np.ndarray,
    g_ulw: np.ndarray,
    w_extra: np.ndarray,
) -> float:
    y = g_obs - g_gas - g_ulw
    x = g_star
    w = (1.0 / np.maximum(eg_obs, 1e-6)) * np.asarray(w_extra)
    num = float(np.nansum(w * x * y))
    den = float(np.nansum(w * x * x))
    if den <= 0:
        return 0.0
    return float(max(num / den, 0.0))


def chi2_accel_w(
    g_obs: np.ndarray,
    eg_obs: np.ndarray,
    g_model: np.ndarray,
    w_extra: np.ndarray,
) -> float:
    w = (1.0 / np.maximum(eg_obs, 1e-6)) * np.asarray(w_extra)
    return float(np.nansum(((g_model - g_obs) * w) ** 2))


def line_bias_accel(
    R: np.ndarray,
    SBdisk: np.ndarray,
    pix_kpc: float,
    size: int,
    line_eps_kpc: float,
    pad_factor: int = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    j = make_axisymmetric_image(R, SBdisk, pix_kpc, size)
    gx, gy = irradiance_log_bias(j, pix_kpc, strength=1.0, eps_kpc=line_eps_kpc, pad_factor=pad_factor)
    rgrid, gr = circular_profile(gx, gy, pix_kpc, nbins=64)
    left_val = float(gr[0]) if np.isfinite(gr[0]) else 0.0
    right_val = float(gr[-1]) if np.isfinite(gr[-1]) else left_val
    g_line = np.interp(R, rgrid, gr, left=left_val, right=right_val)
    return g_line, rgrid


def compute_inv1_unit(
    kind: str,
    rc,
    pix_kpc: float,
    size: int,
    line_eps_kpc: float,
    pad_factor: int,
    rod_L_kpc: float | None = None,
    rod_angle_deg: float | None = None,
):
    kind = (kind or 'fft').lower()
    if kind == 'disk_analytic':
        # interpolate SBdisk(R) and integrate ring kernel
        import numpy as _np
        R = rc.R
        SB = rc.SBdisk
        def Sigma_of_R(rho: _np.ndarray) -> _np.ndarray:
            return _np.interp(rho, R, SB, left=SB[0], right=SB[-1])
        g_line = disk_inv1_gr(R, Sigma_of_R, eps=line_eps_kpc)
        return g_line
    elif kind == 'rod_analytic':
        # Build grid then circular average
        ny = nx = size
        y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
        x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
        xx, yy = np.meshgrid(x, y, indexing='xy')
        L = float(rod_L_kpc or (2.0 * np.nanmax(rc.R)))
        ang = float(rod_angle_deg or 0.0)
        gx, gy = rod_inv1_field_xy(xx, yy, L=L, eps=line_eps_kpc, lam0=1.0, angle_deg=ang)
        from src.models.fdbl import circular_profile as _cprof
        rgrid, gr = _cprof(gx, gy, pix_kpc, nbins=64)
        left_val = float(gr[0]) if np.isfinite(gr[0]) else 0.0
        right_val = float(gr[-1]) if np.isfinite(gr[-1]) else left_val
        g_line = np.interp(rc.R, rgrid, gr, left=left_val, right=right_val)
        return g_line
    else:
        g_line, _ = line_bias_accel(rc.R, rc.SBdisk, pix_kpc, size, line_eps_kpc, pad_factor)
        return g_line

def _nice_ticks(vmin: float, vmax: float, ntarget: int = 5):
    import math
    if not (math.isfinite(vmin) and math.isfinite(vmax)):
        return []
    if vmax <= vmin:
        vmax = vmin + 1.0
    span = vmax - vmin
    raw = span / max(ntarget, 1)
    mag = 10 ** math.floor(math.log10(raw))
    norm = raw / mag
    if norm <= 1:
        step = 1 * mag
    elif norm <= 2:
        step = 2 * mag
    elif norm <= 2.5:
        step = 2.5 * mag
    elif norm <= 5:
        step = 5 * mag
    else:
        step = 10 * mag
    start = math.floor(vmin / step) * step
    ticks = []
    x = start
    while x <= vmax + 1e-9:
        if x >= vmin - 1e-9:
            ticks.append(x)
        x += step
    return ticks


def svg_overlay(
    R: np.ndarray,
    V: np.ndarray,
    eV: np.ndarray,
    Vgr: np.ndarray,
    Vulw: np.ndarray,
    info: str,
    show_resid: bool = True,
    res_height: int = 160,
) -> str:
    W, H_main, H_res = 720, 420, int(res_height)
    H = H_main + (H_res if show_resid else 0)
    pad = 48
    xmin, xmax = 0.0, float(np.nanmax(R) * 1.05)
    ymin, ymax = 0.0, float(max(np.nanmax(V), np.nanmax(Vulw), np.nanmax(Vgr))
                            * 1.15)

    def xmap(x):
        return pad + (W - 2 * pad) * (x - xmin) / (xmax - xmin + 1e-12)

    def ymap(y):
        return H_main - pad - (H_main - 2 * pad) * (y - ymin) / (ymax - ymin + 1e-12)

    # 差分の大きさを評価（重なり検出用）
    try:
        dv = np.nanmax(np.abs(Vulw - Vgr))
    except Exception:
        dv = np.nan
    overlap_note = ""
    overlap = False
    # しきい値: 速度差が 0.5 km/s 未満なら視覚的にほぼ同一
    if np.isfinite(dv) and dv < 0.5:
        overlap = True
        overlap_note = f" (curves overlap: ΔV_max≈{dv:.2f} km/s)"

    # ticks for main axes
    xticks = _nice_ticks(xmin, xmax, ntarget=6)
    yticks = _nice_ticks(ymin, ymax, ntarget=6)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" '
        f'height="{H}">',
        '<style>text{font-family:system-ui;font-size:12px} .grid{stroke:#eee} .tick{stroke:#888}</style>',
        f'<text x="{pad}" y="22">{info}{overlap_note}</text>',
        f'<line x1="{pad}" y1="{H_main-pad}" x2="{W-pad}" y2="{H_main-pad}" '
        'stroke="#444"/>',
        f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{H-pad}" '
        'stroke="#444"/>',
        f'<text x="{W/2-20:.0f}" y="{H_main-10}">R [kpc]</text>',
        f'<text x="10" y="{H/2}">V [km/s]</text>',
    ]
    # grid and ticks for main plot
    for xv in xticks:
        x = xmap(xv)
        parts.append(f'<line class="grid" x1="{x:.2f}" y1="{pad}" x2="{x:.2f}" y2="{H_main-pad}" />')
        parts.append(f'<line class="tick" x1="{x:.2f}" y1="{H_main-pad}" x2="{x:.2f}" y2="{H_main-pad+6}" />')
        parts.append(f'<text x="{x-8:.0f}" y="{H_main-pad+20:.0f}">{xv:.0f}</text>')
    for yv in yticks:
        y = ymap(yv)
        parts.append(f'<line class="grid" x1="{pad}" y1="{y:.2f}" x2="{W-pad}" y2="{y:.2f}" />')
        parts.append(f'<line class="tick" x1="{pad-6}" y1="{y:.2f}" x2="{pad}" y2="{y:.2f}" />')
        parts.append(f'<text x="{pad-40}" y="{y+4:.0f}">{yv:.0f}</text>')
    # data
    for r, v, ev in zip(R, V, eV):
        x = xmap(r)
        y = ymap(v)
        e0, e1 = ymap(v - ev), ymap(v + ev)
        parts.append(
            f'<line x1="{x:.2f}" y1="{e0:.2f}" x2="{x:.2f}" '
            f'y2="{e1:.2f}" stroke="#888"/>'
        )
        parts.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2.2" fill="#111" />'
        )
    # curves
    path_gr = "M " + " ".join(
        f"{xmap(r):.2f},{ymap(v):.2f}" for r, v in zip(R, Vgr)
    )
    # GR: 破線＋やや細めで重なり時にも識別しやすく
    parts.append(
        f'<path d="{path_gr}" fill="none" stroke="#d62728" '
        f'stroke-width="2" stroke-dasharray="6 4" opacity="{0.9 if not overlap else 0.8}" />'
    )
    path_ulw = "M " + " ".join(
        f"{xmap(r):.2f},{ymap(v):.2f}" for r, v in zip(R, Vulw)
    )
    # ULW: 実線＋わずかに太め
    parts.append(
        f'<path d="{path_ulw}" fill="none" stroke="#1f77b4" '
        f'stroke-width="{2.5 if overlap else 2}" opacity="{0.95 if not overlap else 0.9}" />'
    )
    parts.append(
        '<rect x="520" y="54" width="180" height="52" '
        'fill="#fff" stroke="#888"/>'
    )
    parts.append(
        '<line x1="530" y1="70" x2="560" y2="70" '
        'stroke="#d62728" stroke-width="2" stroke-dasharray="6 4" />'
    )
    parts.append('<text x="565" y="74">GR(no DM)</text>')
    parts.append(
        '<line x1="530" y1="92" x2="560" y2="92" '
        'stroke="#1f77b4" stroke-width="2.5" />'
    )
    parts.append('<text x="565" y="96">ULW-EM</text>')
    # residual panel under the main plot
    if show_resid:
        y0 = H_main
        # compute residuals
        Vres_gr = Vgr - V
        Vres_ulw = Vulw - V
        # autoscale with some padding
        rmin = float(np.nanmin([np.nanmin(Vres_gr), np.nanmin(Vres_ulw), 0.0]))
        rmax = float(np.nanmax([np.nanmax(Vres_gr), np.nanmax(Vres_ulw), 0.0]))
        rgap = max(rmax - rmin, 1e-6)
        rpad = 0.1 * rgap
        rmin -= rpad; rmax += rpad
        def ymapr(y):
            return y0 + H_res - pad - (H_res - 2 * pad) * (y - rmin) / (rmax - rmin + 1e-12)
        # axes
        parts.append(
            f'<line x1="{pad}" y1="{y0+H_res-pad}" x2="{W-pad}" y2="{y0+H_res-pad}" stroke="#444"/>'
        )
        parts.append(
            f'<line x1="{pad}" y1="{y0+pad}" x2="{pad}" y2="{y0+H_res-pad}" stroke="#444"/>'
        )
        parts.append(f'<text x="{W/2-26:.0f}" y="{y0+H_res-10}">R [kpc]</text>')
        parts.append(f'<text x="10" y="{y0+H_res/2}">ΔV [km/s]</text>')
        # ticks and grid for residuals
        xt_r = xticks
        yt_r = _nice_ticks(rmin, rmax, ntarget=5)
        for xv in xt_r:
            x = xmap(xv)
            parts.append(f'<line class="grid" x1="{x:.2f}" y1="{y0+pad}" x2="{x:.2f}" y2="{y0+H_res-pad}" />')
            parts.append(f'<line class="tick" x1="{x:.2f}" y1="{y0+H_res-pad}" x2="{x:.2f}" y2="{y0+H_res-pad+6}" />')
            parts.append(f'<text x="{x-8:.0f}" y="{y0+H_res-pad+20:.0f}">{xv:.0f}</text>')
        for yv in yt_r:
            y = ymapr(yv)
            parts.append(f'<line class="grid" x1="{pad}" y1="{y:.2f}" x2="{W-pad}" y2="{y:.2f}" />')
            parts.append(f'<line class="tick" x1="{pad-6}" y1="{y:.2f}" x2="{pad}" y2="{y:.2f}" />')
            parts.append(f'<text x="{pad-46}" y="{y+4:.0f}">{yv:.0f}</text>')
        # zero line
        yzero = ymapr(0.0)
        parts.append(f'<line x1="{pad}" y1="{yzero:.2f}" x2="{W-pad}" y2="{yzero:.2f}" stroke="#bbb"/>')
        # curves
        pgr = "M " + " ".join(f"{xmap(r):.2f},{ymapr(v):.2f}" for r, v in zip(R, Vres_gr))
        pulw = "M " + " ".join(f"{xmap(r):.2f},{ymapr(v):.2f}" for r, v in zip(R, Vres_ulw))
        parts.append(f'<path d="{pgr}" fill="none" stroke="#d62728" stroke-dasharray="6 4" opacity="0.8" />')
        parts.append(f'<path d="{pulw}" fill="none" stroke="#1f77b4" opacity="0.9" />')
        parts.append(f'<text x="{pad}" y="{y0+pad-6}">Residuals: ULW-obs (blue), GR-obs (red dashed)</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="SPARC銀河名 (例: DDO154)")
    ap.add_argument(
        "--mrt",
        type=Path,
        default=Path("data/sparc/MassModels_Lelli2016c.mrt"),
    )
    ap.add_argument("--pix", type=float, default=0.2)
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--err-floor-kms", type=float, default=5.0,
                    help="速度誤差の下限[km/s]（egに変換して適用）")
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("paper/figures/compare_fit.svg"),
    )
    ap.add_argument("--boost", type=float, default=0.0,
                    help="構造ブースト強度alpha (0で無効)")
    ap.add_argument("--boost-s1", type=float, default=0.5,
                    help="ブーストの内側スケール[kpc]")
    ap.add_argument("--boost-s2", type=float, default=1.5,
                    help="ブーストの外側スケール[kpc]")
    ap.add_argument("--boost-tie-lam", action="store_true",
                    help="σ1,σ2をλに比例(σ1≈λ/8, σ2≈λ/3)させる")
    ap.add_argument("--plane-alpha", type=float, default=0.0,
                    help="円盤面1/r風バイアスの強度")
    ap.add_argument("--plane-r0", type=float, default=1.0,
                    help="円盤面1/rのソフトニング長[kpc]")
    ap.add_argument("--bar-alpha", type=float, default=0.0,
                    help="棒軸1/r風バイアスの強度")
    ap.add_argument("--bar-angle", type=float, default=0.0,
                    help="棒の角度[deg] (画像座標系)")
    ap.add_argument("--bar-width", type=float, default=1.0,
                    help="棒の幅(ガウシアンσ)[kpc]")
    ap.add_argument("--bar-r0", type=float, default=1.0,
                    help="棒軸1/rのソフトニング長[kpc]")
    ap.add_argument("--irr-alpha", type=float, default=0.0,
                    help="照度由来の追加FDB強度(0で無効)")
    ap.add_argument("--irr-eps", type=float, default=0.3,
                    help="照度核のソフトニングε[kpc]")
    ap.add_argument("--irr-p", type=float, default=2.0,
                    help="照度核の指数p(既定2: 1/r^2)")
    # advanced kernel options
    ap.add_argument("--aniso-q", type=float, default=1.0,
                    help="異方Yukawaの軸比q(=1等方、<1扁平)")
    ap.add_argument("--aniso-angle", type=float, default=0.0,
                    help="異方Yukawaの角度[deg]")
    ap.add_argument("--nl-gamma", type=float, default=0.0,
                    help="非線形源カップリングの強度γ(>0で有効)")
    ap.add_argument("--nl-q", type=float, default=1.0,
                    help="非線形の冪指数q")
    ap.add_argument("--nl-iter", type=int, default=2,
                    help="非線形反復回数")
    ap.add_argument("--out-alpha", type=float, default=0.0,
                    help="外縁強調の半径重み強度")
    ap.add_argument("--out-r0", type=float, default=1.0,
                    help="外縁強調のr0[kpc]")
    ap.add_argument("--auto-geo", action="store_true",
                    help="data/imaging/geometry.jsonのPA/軸比を自動適用")
    ap.add_argument("--pad-factor", type=int, default=2,
                    help="FFT解のゼロパディング係数(>=1)")
    ap.add_argument("--outer-frac", type=float, default=0.6,
                    help="max(R)に対する外縁閾値(例0.6)")
    ap.add_argument("--outer-weight", type=float, default=1.0,
                    help="外縁点へ掛ける追加重み(例1.0で2倍)")
    ap.add_argument("--eg-frac-floor", type=float, default=0.0,
                    help="加速度誤差の相対下限(eg_eff^2 = eg^2 + (f*g)^2)")
    ap.add_argument("--eg-abs-floor", type=float, default=0.0,
                    help="加速度誤差の絶対下限(同上に加算)")
    ap.add_argument("--lam-grid", type=str, default="2,3,5,8,12,15,20",
                    help="λグリッド(kpc,カンマ区切り)")
    ap.add_argument("--A-grid", type=str, default="0.01,0.0316,0.1,0.316,1,3.16,10,31.6,100,316",
                    help="Aグリッド(カンマ区切り)")
    ap.add_argument("--mix-lam-ratio", type=float, default=0.0,
                    help="2帯域混合: lam2 = ratio * lam (0で無効)")
    ap.add_argument("--mix-w", type=float, default=0.0,
                    help="2帯域混合の重み(0..1, 0で無効)")
    ap.add_argument("--line-eps", type=float, default=0.5,
                    help="1/r型(FDB_line)のソフトニング長ε[kpc]")
    ap.add_argument("--inv1-kind", type=str, default="fft",
                    help="1/r項の計算方式: fft|disk_analytic|rod_analytic")
    ap.add_argument("--rod-L", type=float, default=0.0,
                    help="rod_analytic時の棒長[kpc](0で自動: ~2*Rmax)")
    ap.add_argument("--rod-angle", type=float, default=0.0,
                    help="rod_analytic時の棒角度[deg]")
    ap.add_argument("--mu-min", type=float, default=0.2,
                    help="星M/L(mu)の下限")
    ap.add_argument("--mu-max", type=float, default=0.8,
                    help="星M/L(mu)の上限")
    ap.add_argument("--inv1-orth", action="store_true",
                    help="1/r項を星加速度に直交化して多重共線性を回避")
    # fixed shared-params mode
    ap.add_argument("--fixed-lam", type=float, default=None,
                    help="固定λ[kpc]（指定時はグリッド探索を抑制）")
    ap.add_argument("--fixed-A", type=float, default=None,
                    help="固定A（指定時はグリッド探索を抑制）")
    ap.add_argument("--gas-scale", type=float, default=1.0,
                    help="ガス加速度のスケール(ULW時に適用)")
    ap.add_argument("--res-height", type=int, default=160,
                    help="残差(ΔV)パネルの高さ[px] (既定160; 以前より拡大)")
    args = ap.parse_args()

    rc = read_sparc_massmodels(args.mrt, args.name)
    # optional auto-geometry override
    if args.auto_geo:
        from pathlib import Path as _Path
        import json as _json
        gj = _Path("data/imaging/geometry.json")
        if gj.exists():
            try:
                geo = _json.loads(gj.read_text(encoding="utf-8"))
                if rc.name in geo:
                    info = geo[rc.name]
                    args.aniso_q = float(info.get("q", args.aniso_q))
                    args.aniso_angle = float(info.get("pa_deg", args.aniso_angle))
                    # use same PA for bar by default
                    args.bar_angle = float(info.get("pa_deg", args.bar_angle))
            except Exception:
                pass
    obs = to_accel(rc.R, rc.Vobs, rc.eV)
    # error floors
    if args.eg_frac_floor > 0.0 or args.eg_abs_floor > 0.0:
        eg2 = obs.eg * obs.eg + (args.eg_frac_floor * obs.g) ** 2 + (args.eg_abs_floor ** 2)
        obs = Obs(R=obs.R, V=obs.V, eV=obs.eV, g=obs.g, eg=np.sqrt(np.maximum(eg2, 1e-12)))
    g_gas = rc.Vgas * rc.Vgas / np.maximum(rc.R, 1e-6)
    vstar2 = rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul
    g_star = vstar2 / np.maximum(rc.R, 1e-6)

    # outer weighting mask
    thr = float(np.nanmax(rc.R)) * args.outer_frac
    w_outer = 1.0 + args.outer_weight * (rc.R >= thr)

    # GR-only: mu best (外縁重み入り)
    mu_gr = fit_mu_linear_w(obs.g, obs.eg, g_gas, g_star, 0.0 * obs.g, w_outer)
    g_gr = g_gas + mu_gr * g_star
    c2_gr = chi2_accel_w(obs.g, obs.eg, g_gr, w_outer)
    Vgr = np.sqrt(np.clip(g_gr * rc.R, 0.0, None))

    # ULW grid search (lam,A), mu solved per grid
    best = (np.inf, np.nan, np.nan, np.nan)  # chi2, lam, A, mu
    lam_list = [float(x) for x in args.lam_grid.split(',') if x]
    A_list = [float(x) for x in args.A_grid.split(',') if x]
    if args.fixed_lam is not None:
        lam_list = [float(args.fixed_lam)]
    if args.fixed_A is not None:
        A_list = [float(args.fixed_A)]
    # Precompute line-bias unit acceleration (strength=1)
    g_line_unit = compute_inv1_unit(
        args.inv1_kind, rc, pix_kpc=args.pix, size=args.size,
        line_eps_kpc=args.line_eps, pad_factor=args.pad_factor,
        rod_L_kpc=(args.rod_L if args.rod_L>0 else None),
        rod_angle_deg=args.rod_angle,
    )

    for lam in lam_list:
        s1 = (lam / 8.0) if args.boost_tie_lam else args.boost_s1
        s2 = (lam / 3.0) if args.boost_tie_lam else args.boost_s2
        lam2 = (args.mix_lam_ratio * lam) if args.mix_lam_ratio > 0 else None
        g_ulw, _ = model_ulw_accel(
            rc.R, rc.SBdisk, lam, A=1.0, pix_kpc=args.pix, size=args.size,
            boost=args.boost, boost_s1_kpc=s1, boost_s2_kpc=s2,
            plane_alpha=args.plane_alpha, plane_r0_kpc=args.plane_r0,
            bar_alpha=args.bar_alpha, bar_angle_deg=args.bar_angle,
            bar_width_kpc=args.bar_width, bar_r0_kpc=args.bar_r0,
            irr_alpha=args.irr_alpha, irr_eps_kpc=args.irr_eps,
            irr_p=args.irr_p, aniso_q=args.aniso_q,
            aniso_angle=args.aniso_angle,
            nl_gamma=args.nl_gamma, nl_q=args.nl_q, nl_iter=args.nl_iter,
            out_alpha=args.out_alpha, out_r0_kpc=args.out_r0,
            pad_factor=args.pad_factor,
            lam2_kpc=lam2, mix_w=max(0.0, min(args.mix_w, 1.0)),
        )
        # error floor (eg)
        if args.err_floor_kms and args.err_floor_kms > 0:
            eg_eff = np.maximum(obs.eg, 2.0 * rc.Vobs * args.err_floor_kms / np.maximum(rc.R, 1e-6))
        else:
            eg_eff = obs.eg
        # scale g_ulw by A: try logspace（alpha_lineは撤去方針のため推定しない）
        for A in A_list:
            g_ulw_A = A * g_ulw
            # Solve 1-parameter WLS for [mu]（alpha_lineは0固定）
            # apply gas scale for ULW model fitting
            gg_ulw = args.gas_scale * g_gas
            y = obs.g - gg_ulw - g_ulw_A
            x1 = g_star
            x2 = np.zeros_like(g_star)
            w = (1.0 / np.maximum(eg_eff, 1e-6)) * w_outer
            # Optional orthogonalization to mitigate collinearity (x2 ⟂ x1)
            if getattr(args, 'inv1_orth', False):
                a11o = float(np.nansum(w * x1 * x1)) + 1e-12
                proj = (float(np.nansum(w * x2 * x1)) / a11o) * x1
                x2_eff = x2 - proj
            else:
                x2_eff = x2
            a11 = float(np.nansum(w * x1 * x1))
            a22 = float(np.nansum(w * x2_eff * x2_eff)) + 1e-12
            a12 = float(np.nansum(w * x1 * x2_eff))
            b1 = float(np.nansum(w * x1 * y))
            b2 = float(np.nansum(w * x2_eff * y))
            det = a11 * a22 - a12 * a12 + 1e-12
            mu = max(min((b1 * a22 - b2 * a12) / det, args.mu_max), args.mu_min)
            alpha_line = 0.0
            g_model = gg_ulw + mu * g_star + g_ulw_A
            c2 = chi2_accel_w(obs.g, eg_eff, g_model, w_outer)
            if c2 < best[0]:
                best = (c2, lam, A, mu, alpha_line)

    c2_ulw, lam_b, A_b, mu_ulw, alpha_b = best
    # assemble curves
    s1 = (lam_b / 8.0) if args.boost_tie_lam else args.boost_s1
    s2 = (lam_b / 3.0) if args.boost_tie_lam else args.boost_s2
    g_ulw_final, _ = model_ulw_accel(
        rc.R, rc.SBdisk, lam_b, A=1.0, pix_kpc=args.pix, size=args.size,
        boost=args.boost, boost_s1_kpc=s1, boost_s2_kpc=s2,
        plane_alpha=args.plane_alpha, plane_r0_kpc=args.plane_r0,
        bar_alpha=args.bar_alpha, bar_angle_deg=args.bar_angle,
        bar_width_kpc=args.bar_width, bar_r0_kpc=args.bar_r0,
        irr_alpha=args.irr_alpha, irr_eps_kpc=args.irr_eps,
        irr_p=args.irr_p, aniso_q=args.aniso_q,
        aniso_angle=args.aniso_angle,
        nl_gamma=args.nl_gamma, nl_q=args.nl_q, nl_iter=args.nl_iter,
        out_alpha=args.out_alpha, out_r0_kpc=args.out_r0,
        pad_factor=args.pad_factor,
    )
    # line term廃止（μ(k)へ統合方針）。alpha_b=0固定。
    g_model = args.gas_scale * g_gas + mu_ulw * g_star + A_b * g_ulw_final
    Vulw = np.sqrt(np.clip(g_model * rc.R, 0.0, None))

    # AIC (k params)
    n = len(rc.R)
    k_gr = 1
    k_ulw = 2  # [mu, A]（lamは共有で別途カウントする運用に変更予定）
    # AICc = chi2 + 2k + 2k(k+1)/(n-k-1)
    def aicc(chi2: float, n: int, k: int) -> float:
        base = chi2 + 2.0 * k
        denom = (n - k - 1)
        return base + (2.0 * k * (k + 1)) / denom if denom > 0 else base
    aic_gr = aicc(c2_gr, n, k_gr)
    aic_ulw = aicc(c2_ulw, n, k_ulw)

    info = (
        f"{rc.name} | GR(mu={mu_gr:.3g}, chi2={c2_gr:.3g}, AIC={aic_gr:.2f}) "
        f"| ULW(lam={lam_b:.3g}kpc, A={A_b:.3g}, mu={mu_ulw:.3g}, "
        f"chi2={c2_ulw:.3g}, AIC={aic_ulw:.2f}, boost={args.boost})"
    )
    svg = svg_overlay(
        rc.R, rc.Vobs, rc.eV, Vgr, Vulw, info,
        show_resid=True, res_height=int(getattr(args, 'res_height', 160))
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg, encoding="utf-8")
    print(info)
    print(f"saved: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
