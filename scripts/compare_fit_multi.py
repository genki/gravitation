#!/usr/bin/env python3
"""
複数銀河に対し、ULW-EM(FDB)のグローバル(λ,A)を共有して同時フィット。
各銀河のmu([3.6]のM/L相当)は解析的に最小二乗で求める。

併せてGR(no DM)ベースライン(各銀河ごとにmuのみ)と総χ²を比較する。

出力: JSONサマリ(data/results/multi_fit.json)と標準出力ログ。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from datetime import datetime, timezone
import time

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
from src.fdb.angle_kernels import radial_forwardize


def to_accel(R: np.ndarray, V: np.ndarray, eV: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    Rm = np.maximum(R, 1e-6)
    g = (V * V) / Rm
    eg = 2.0 * V * np.maximum(eV, 1e-6) / Rm
    return g, eg


def model_ulw_accel(
    R: np.ndarray,
    SBdisk: np.ndarray,
    lam_kpc: float,
    A: float,
    pix_kpc: float,
    size: int,
    boost: float,
    s1_kpc: float,
    s2_kpc: float,
    plane_alpha: float = 0.0,
    plane_r0_kpc: float = 1.0,
    bar_alpha: float = 0.0,
    bar_angle_deg: float = 0.0,
    bar_width_kpc: float = 1.0,
    bar_r0_kpc: float = 1.0,
    irr_alpha: float = 0.0,
    irr_eps_kpc: float = 0.3,
    irr_p: float = 2.0,
    aniso_q: float = 1.0,
    aniso_angle: float = 0.0,
    nl_gamma: float = 0.0,
    nl_q: float = 1.0,
    nl_iter: int = 0,
    out_alpha: float = 0.0,
    out_r0_kpc: float = 1.0,
    pad_factor: int = 1,
    lam2_kpc: float | None = None,
    mix_w: float = 0.0,
) -> np.ndarray:
    j = make_axisymmetric_image(R, SBdisk, pix_kpc, size)
    if nl_gamma and nl_gamma > 0.0:
        phi = solve_phi_yukawa_nonlinear(
            j, pix_kpc, lam_kpc, beta=1.0, gamma=nl_gamma,
            power_q=nl_q, n_iter=nl_iter or 2, pad_factor=pad_factor
        )
    elif aniso_q and aniso_q != 1.0:
        phi = solve_phi_yukawa_aniso(
            j, pix_kpc, lam_kpc, beta=1.0, q_axis=aniso_q,
            angle_deg=aniso_angle, pad_factor=pad_factor
        )
    else:
        phi = solve_phi_yukawa_2d(j, pix_kpc, lam_kpc, beta=1.0, pad_factor=pad_factor)
    dpx, dpy = grad_from_phi(phi, pix_kpc)
    gx = -A * dpx
    gy = -A * dpy
    # optional second band mixture
    if (lam2_kpc is not None) and (mix_w > 0.0):
        if nl_gamma and nl_gamma > 0.0:
            phi2 = solve_phi_yukawa_nonlinear(
                j, pix_kpc, lam2_kpc, beta=1.0, gamma=nl_gamma,
                power_q=nl_q, n_iter=nl_iter or 2, pad_factor=pad_factor
            )
        elif aniso_q and aniso_q != 1.0:
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
        s1_pix = s1_kpc / pix_kpc
        s2_pix = s2_kpc / pix_kpc
        F = structure_boost(j, s1_pix, s2_pix, alpha=boost)
        gx *= F
        gy *= F
    if plane_alpha > 0.0:
        Wp = plane_bias_weight(j.shape[1], j.shape[0], pix_kpc,
                               alpha=plane_alpha, r0_kpc=plane_r0_kpc)
        gx *= Wp
        gy *= Wp
    if bar_alpha > 0.0:
        Wb = bar_bias_weight(j.shape[1], j.shape[0], pix_kpc,
                             angle_deg=bar_angle_deg, width_kpc=bar_width_kpc,
                             alpha=bar_alpha, r0_kpc=bar_r0_kpc)
        gx *= Wb
        gy *= Wb
    if irr_alpha > 0.0:
        gx_add, gy_add = irradiance_bias(j, pix_kpc, irr_alpha,
                                         eps_kpc=irr_eps_kpc, p=irr_p)
        gx += gx_add
        gy += gy_add
    if out_alpha > 0.0:
        Wo = radial_outer_boost(j.shape[1], j.shape[0], pix_kpc,
                                alpha=out_alpha, r0_kpc=out_r0_kpc)
        gx *= Wo
        gy *= Wo
    rgrid, gr = circular_profile(gx, gy, pix_kpc, nbins=64)
    # 外挿は端値で埋める（安定化）
    left_val = float(gr[0]) if np.isfinite(gr[0]) else 0.0
    right_val = float(gr[-1]) if np.isfinite(gr[-1]) else left_val
    g_ulw = np.interp(R, rgrid, gr, left=left_val, right=right_val)
    return g_ulw


def line_bias_accel(
    R: np.ndarray,
    SBdisk: np.ndarray,
    pix_kpc: float,
    size: int,
    line_eps_kpc: float,
    pad_factor: int = 1,
    beta_forward: float = 0.0,
    forward_angle_deg: float = 0.0,
) -> np.ndarray:
    j = make_axisymmetric_image(R, SBdisk, pix_kpc, size)
    gx, gy = irradiance_log_bias(
        j, pix_kpc, strength=1.0, eps_kpc=line_eps_kpc, pad_factor=pad_factor,
        beta_forward=beta_forward, forward_angle_deg=forward_angle_deg,
    )
    rgrid, gr = circular_profile(gx, gy, pix_kpc, nbins=64)
    left_val = float(gr[0]) if np.isfinite(gr[0]) else 0.0
    right_val = float(gr[-1]) if np.isfinite(gr[-1]) else left_val
    g_line = np.interp(R, rgrid, gr, left=left_val, right=right_val)
    return g_line


def compute_inv1_unit(
    kind: str,
    R: np.ndarray,
    SB: np.ndarray,
    pix_kpc: float,
    size: int,
    line_eps_kpc: float,
    pad_factor: int,
    rod_L_kpc: float | None = None,
    rod_angle_deg: float | None = None,
    beta_forward: float = 0.0,
    forward_angle_deg: float = 0.0,
) -> np.ndarray:
    kind = (kind or 'fft').lower()
    if kind == 'disk_analytic':
        import numpy as _np
        def Sigma_of_R(rho: _np.ndarray) -> _np.ndarray:
            return _np.interp(rho, R, SB, left=SB[0], right=SB[-1])
        return disk_inv1_gr(R, Sigma_of_R, eps=line_eps_kpc)
    elif kind == 'rod_analytic':
        ny = nx = size
        y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
        x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
        xx, yy = np.meshgrid(x, y, indexing='xy')
        L = float(rod_L_kpc or (2.0 * np.nanmax(R)))
        ang = float(rod_angle_deg or 0.0)
        gx, gy = rod_inv1_field_xy(xx, yy, L=L, eps=line_eps_kpc, lam0=1.0, angle_deg=ang)
        rgrid, gr = circular_profile(gx, gy, pix_kpc, nbins=64)
        left_val = float(gr[0]) if np.isfinite(gr[0]) else 0.0
        right_val = float(gr[-1]) if np.isfinite(gr[-1]) else left_val
        return np.interp(R, rgrid, gr, left=left_val, right=right_val)
    else:
        return line_bias_accel(R, SB, pix_kpc, size, line_eps_kpc, pad_factor,
                               beta_forward=beta_forward, forward_angle_deg=forward_angle_deg)


def _default_progress_path(out: Path) -> Path:
    return out.parent / f"{out.name}.progress.json"


def _jsonify_mus(mus: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for name, vals in mus.items():
        out[name] = {k: float(v) for k, v in vals.items()}
    return out


def _load_progress(progress_path: Path,
                   names: List[str],
                   lam_list: List[float],
                   A_list: List[float],
                   gas_grid: List[float],
                   split_stellar: bool) -> tuple[int, Dict | None, bool]:
    if not progress_path.exists():
        return 0, None, False
    try:
        payload = json.loads(progress_path.read_text(encoding='utf-8'))
    except Exception:
        return 0, None, False
    if payload.get('names') != names:
        return 0, None, False
    if payload.get('lam_grid') != lam_list or payload.get('A_grid') != A_list or payload.get('gas_grid') != gas_grid:
        return 0, None, False
    if bool(payload.get('split_stellar', False)) != bool(split_stellar):
        return 0, None, False
    next_idx = int(payload.get('next_index', 0))
    best = payload.get('best')
    complete = bool(payload.get('complete', False))
    return next_idx, best, complete


def _save_progress(progress_path: Path,
                   names: List[str],
                   lam_list: List[float],
                   A_list: List[float],
                   gas_grid: List[float],
                   split_stellar: bool,
                   next_idx: int,
                   best: Dict | None,
                   total: int,
                   complete: bool) -> None:
    payload = {
        'names': names,
        'lam_grid': lam_list,
        'A_grid': A_list,
        'gas_grid': gas_grid,
        'split_stellar': bool(split_stellar),
        'next_index': int(next_idx),
        'best': best,
        'total_combinations': int(total),
        'complete': bool(complete),
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    progress_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def _precompute_ulw_for_lambda(lam: float,
                               args,
                               galaxies,
                               geo_map: Dict[str, Dict]) -> List[np.ndarray]:
    pre_ulw: List[np.ndarray] = []
    s1 = (lam / 8.0) if args.boost_tie_lam else args.boost_s1
    s2 = (lam / 3.0) if args.boost_tie_lam else args.boost_s2
    for nm, R, SB, g_obs, eg, g_gas, g_disk, g_bul, g_star, w_outer in galaxies:
        aniso_q_g = args.aniso_q
        aniso_ang_g = args.aniso_angle
        bar_ang_g = args.bar_angle
        if (args.auto_geo or args.phys_defaults) and (nm in geo_map):
            ginfo = geo_map.get(nm, {})
            aniso_q_g = float(ginfo.get('q', aniso_q_g))
            aniso_ang_g = float(ginfo.get('pa_deg', aniso_ang_g))
            bar_ang_g = float(ginfo.get('pa_deg', bar_ang_g))
        irr_alpha_g = args.irr_alpha
        if args.phys_defaults:
            irr_alpha_g = args.phys_kappa / max(lam, 1e-6)
        nl_gamma_g = args.nl_gamma
        if args.phys_defaults and (args.phys_nl_gamma > 0.0):
            nl_gamma_g = args.phys_nl_gamma
        lam2 = (args.mix_lam_ratio * lam) if args.mix_lam_ratio > 0 else None
        if args.fdb_mode == 'surface':
            g_ulw_1 = compute_inv1_unit(
                'fft', R, SB, args.pix, args.size, args.line_eps, args.pad_factor,
                beta_forward=float(args.beta_forward or 0.0),
                forward_angle_deg=float(aniso_ang_g or 0.0),
            )
            if (args.beta_forward is not None) and (float(args.beta_forward) > 0.0):
                g_ulw_1 = radial_forwardize(R, g_ulw_1, float(args.beta_forward))
        else:
            g_ulw_1 = model_ulw_accel(
                R, SB, lam, A=1.0, pix_kpc=args.pix, size=args.size,
                boost=args.boost, s1_kpc=s1, s2_kpc=s2,
                plane_alpha=args.plane_alpha, plane_r0_kpc=args.plane_r0,
                bar_alpha=args.bar_alpha, bar_angle_deg=bar_ang_g,
                bar_width_kpc=args.bar_width, bar_r0_kpc=args.bar_r0,
                irr_alpha=irr_alpha_g, irr_eps_kpc=args.irr_eps,
                irr_p=args.irr_p, aniso_q=aniso_q_g,
                aniso_angle=aniso_ang_g,
                nl_gamma=nl_gamma_g, nl_q=args.nl_q, nl_iter=args.nl_iter,
                out_alpha=args.out_alpha, out_r0_kpc=args.out_r0,
                pad_factor=args.pad_factor, lam2_kpc=lam2,
                mix_w=max(0.0, min(args.mix_w, 1.0)),
            )
        pre_ulw.append(g_ulw_1)
    return pre_ulw


def _evaluate_combo(lam: float,
                    A: float,
                    gscale: float,
                    pre_ulw: List[np.ndarray],
                    galaxies,
                    mus_gr: Dict[str, Dict[str, float]],
                    args) -> tuple[float, Dict[str, Dict[str, float]]]:
    cur_mus: Dict[str, Dict[str, float]] = {}
    total = 0.0
    for (nm, R, SB, g_obs, eg, g_gas, g_disk, g_bul, g_star, w_outer), g_ulw_1 in zip(galaxies, pre_ulw):
        g_ulw = A * g_ulw_1
        if args is not None:
            try:
                from core.fdb_kernel import g_of_r as _gofr
                fac = 1.0 - 0.5 * float(getattr(args, 'aniso_lambda', 0.0) or 0.0) * _gofr(
                    R,
                    float(getattr(args, 'aniso_ell0_kpc', 0.0) or 0.0),
                    int(getattr(args, 'aniso_m', 2) or 2),
                )
                g_ulw = g_ulw * fac
            except Exception:
                pass
        gg = gscale * g_gas
        if args.split_stellar:
            x1, x2 = g_disk, g_bul
            y = g_obs - gg - g_ulw
            w = (1.0 / np.maximum(eg, 1e-6)) * w_outer
            a11 = float(np.nansum(w * x1 * x1))
            a22 = float(np.nansum(w * x2 * x2))
            a12 = float(np.nansum(w * x1 * x2))
            b1 = float(np.nansum(w * x1 * y))
            b2 = float(np.nansum(w * x2 * y))
            det = a11 * a22 - a12 * a12 + 1e-12
            mu_d = max(min((b1 * a22 - b2 * a12) / det, args.mu_max), args.mu_min)
            mu_b = max(min((b2 * a11 - b1 * a12) / det, args.mu_max), args.mu_min)
            g_model = gg + mu_d * g_disk + mu_b * g_bul + g_ulw
            cur_mus[nm] = {'mu_d': float(mu_d), 'mu_b': float(mu_b)}
        else:
            x1 = g_star
            x2 = np.zeros_like(x1)
            y2 = g_obs - gg - g_ulw
            w = (1.0 / np.maximum(eg, 1e-6)) * w_outer
            if args.inv1_orth:
                a11o = float(np.nansum(w * x1 * x1)) + 1e-12
                proj = (float(np.nansum(w * x2 * x1)) / a11o) * x1
                x2 = x2 - proj
            a11 = float(np.nansum(w * x1 * x1))
            a22 = float(np.nansum(w * x2 * x2)) + 1e-12
            a12 = float(np.nansum(w * x1 * x2))
            b1 = float(np.nansum(w * x1 * y2))
            b2 = float(np.nansum(w * x2 * y2))
            det = a11 * a22 - a12 * a12 + 1e-12
            mu = max(min((b1 * a22 - b2 * a12) / det, args.mu_max), args.mu_min)
            g_model = gg + mu * g_star + g_ulw
            cur_mus[nm] = {'mu': float(mu)}
        total += chi2(g_obs, eg, g_model)
    return float(total), cur_mus


def fit_mu_linear(g_obs: np.ndarray, eg_obs: np.ndarray, g_gas: np.ndarray, g_star: np.ndarray, g_ulw: np.ndarray) -> float:
    y = g_obs - g_gas - g_ulw
    x = g_star
    w = 1.0 / np.maximum(eg_obs, 1e-6)
    num = np.nansum(w * x * y)
    den = np.nansum(w * x * x)
    if den <= 0:
        return 0.0
    return float(max(num / den, 0.0))


def chi2(g_obs: np.ndarray, eg_obs: np.ndarray, g_model: np.ndarray) -> float:
    w = 1.0 / np.maximum(eg_obs, 1e-6)
    return float(np.nansum(((g_model - g_obs) * w) ** 2))


def count_points(g_obs: np.ndarray, eg_obs: np.ndarray, g_model: np.ndarray) -> int:
    m = np.isfinite(g_obs) & np.isfinite(eg_obs) & np.isfinite(g_model)
    return int(np.sum(m))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*", help="銀河名の列 (例: DDO154 NGC2403)")
    ap.add_argument("--names-file", type=Path)
    ap.add_argument("--mrt", type=Path, default=Path("data/sparc/MassModels_Lelli2016c.mrt"))
    ap.add_argument("--pix", type=float, default=0.2)
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--boost", type=float, default=0.0)
    ap.add_argument("--boost-tie-lam", action="store_true")
    ap.add_argument("--boost-s1", type=float, default=0.5)
    ap.add_argument("--boost-s2", type=float, default=1.5)
    ap.add_argument("--out", type=Path, default=Path("data/results/multi_fit.json"))
    # anisotropy/irradiance options (global)
    ap.add_argument("--plane-alpha", type=float, default=0.0)
    ap.add_argument("--plane-r0", type=float, default=1.0)
    ap.add_argument("--bar-alpha", type=float, default=0.0)
    ap.add_argument("--bar-angle", type=float, default=0.0)
    ap.add_argument("--bar-width", type=float, default=1.0)
    ap.add_argument("--bar-r0", type=float, default=1.0)
    ap.add_argument("--irr-alpha", type=float, default=0.0)
    ap.add_argument("--irr-eps", type=float, default=0.3)
    ap.add_argument("--irr-p", type=float, default=2.0)
    ap.add_argument("--aniso-q", type=float, default=1.0)
    ap.add_argument("--aniso-angle", type=float, default=0.0)
    ap.add_argument("--nl-gamma", type=float, default=0.0)
    ap.add_argument("--nl-q", type=float, default=1.0)
    ap.add_argument("--nl-iter", type=int, default=0)
    ap.add_argument("--out-alpha", type=float, default=0.0)
    ap.add_argument("--out-r0", type=float, default=1.0)
    ap.add_argument("--pad-factor", type=int, default=2,
                    help="FFT解のゼロパディング係数(>=1)")
    # --line-eps は重複定義を避ける（上で一度だけ定義）
    ap.add_argument("--inv1-kind", type=str, default="fft",
                    help="1/r項の計算方式: fft|disk_analytic|rod_analytic")
    ap.add_argument("--rod-L", type=float, default=0.0,
                    help="rod_analytic時の棒長[kpc](0で自動)")
    ap.add_argument("--rod-angle", type=float, default=0.0,
                    help="rod_analytic時の棒角度[deg]")
    ap.add_argument("--inv1-orth", action="store_true",
                    help="1/r項を星加速度に直交化して多重共線性を回避")
    ap.add_argument("--line-eps", type=float, default=0.5,
                    help="1/r型(FDB_line)のソフトニング長ε[kpc]")
    # Terminology alias: ULM branches (P: propagating ≈ volumetric, D: diffusive ≈ surface)
    ap.add_argument("--ulm", type=str, choices=["p", "d"], default=None,
                    help="ULM branch alias: p=ULM-P(≒volumetric), d=ULM-D(≒surface). Maps to --fdb-mode.")
    ap.add_argument("--eg-frac-floor", type=float, default=0.0,
                    help="加速度誤差の相対下限(eg_eff^2 = eg^2 + (f*g)^2)")
    ap.add_argument("--eg-abs-floor", type=float, default=0.0,
                    help="加速度誤差の絶対下限(同上に加算)")
    ap.add_argument("--err-floor-kms", type=float, default=5.0,
                    help="速度誤差の下限[km/s]（egに変換して適用）")
    # Robust/uncertainty options
    ap.add_argument("--robust", type=str, default="none",
                    help="外れ値耐性: none|huber|student")
    ap.add_argument("--floor-jitter-kms", type=float, default=0.0,
                    help="誤差へ加える微少jitter[km/s]（rχ²整列用）")
    ap.add_argument("--rho-block", type=float, default=0.0,
                    help="半径方向の相関近似（誤差膨張係数に反映）")
    ap.add_argument("--psf-sigma-kpc", type=float, default=0.0,
                    help="ULW加速度の半径方向ガウス平滑σ[kpc]（簡易PSF）")
    ap.add_argument("--aniso-lambda", type=float, default=0.0,
                    help="異方強度λ_aniso（0で無効）")
    ap.add_argument("--aniso-ell0-kpc", type=float, default=0.0,
                    help="異方スケールℓ0[kpc]（0で無効）")
    ap.add_argument("--aniso-m", type=int, default=2,
                    help="異方指数m(>=2)")
    ap.add_argument("--lam-grid", type=str, default="2,3,5,8,12,15,20",
                    help="λグリッド(kpc,カンマ区切り)")
    ap.add_argument("--A-grid", type=str, default="0.01,0.0316,0.1,0.316,1,3.16,10,31.6,100,316",
                    help="Aグリッド(カンマ区切り)")
    # μ(k) 共有パラメータの粗格子（第1弾: メタデータとして推定・保存）
    ap.add_argument("--mu-eps-grid", type=str, default="0.1,0.3,1.0",
                    help="μ(k)のεグリッド(カンマ区切り)")
    ap.add_argument("--mu-k0-grid", type=str, default="0.02,0.05,0.1,0.2,0.5",
                    help="μ(k)のk0グリッド(カンマ区切り; ~1/λ の次元)")
    ap.add_argument("--mu-m-grid", type=str, default="2,3,4",
                    help="μ(k)のmグリッド(カンマ区切り; m≳2 推奨)")
    ap.add_argument("--mix-lam-ratio", type=float, default=0.0,
                    help="2帯域混合: lam2 = ratio * lam (0で無効)")
    ap.add_argument("--mix-w", type=float, default=0.0,
                    help="2帯域混合の重み(0..1, 0で無効)")
    ap.add_argument("--fdb-mode", type=str, default="ulw", choices=["ulw","surface"],
                    help="FDB追加成分: 'ulw'（既定のULW-Yukawa）/ 'surface'（界面Σ→1/r核の近似）")
    ap.add_argument("--beta-forward", type=float, default=0.0,
                    help="前方化β（0..1, 0=Lambert）。現在は近似スカラー係数として扱う")
    ap.add_argument("--auto-geo", action="store_true",
                    help="data/imaging/geometry.jsonからPA,軸比を自動適用")
    # physically-consistent defaults toggle
    ap.add_argument(
        "--phys-defaults", action="store_true",
        help=(
            "FDB整合の既定値: 自動幾何(異方Yukawa)と照度項をλ依存で有効化"
        ),
    )
    ap.add_argument(
        "--phys-kappa", type=float, default=0.3,
        help=(
            "照度強度の係数κ。irr_strength = κ/λ としてAで同時にスケール"
        ),
    )
    ap.add_argument(
        "--phys-nl-gamma", type=float, default=0.0,
        help=(
            "非線形カップリングγの既定値(>0で1–2回の反復を適用)"
        ),
    )
    # mu prior bounds
    ap.add_argument("--mu-min", type=float, default=0.2,
                    help="星M/L(mu)の下限(またはmu_d,mu_bにも適用)")
    ap.add_argument("--mu-max", type=float, default=0.8,
                    help="星M/L(mu)の上限(またはmu_d,mu_bにも適用)")
    # outer-radius weighting
    ap.add_argument("--outer-frac", type=float, default=0.6,
                    help="max(R)に対するしきい(例0.6)")
    ap.add_argument("--outer-weight", type=float, default=1.0,
                    help="外側に掛ける追加重み(例1.0で2倍)")
    # gas scaling
    ap.add_argument("--gas-scale-grid", type=str, default="1.0,1.33",
                    help="カンマ区切りのgasスケール候補 (例 1.0,1.33)")
    # stellar split
    ap.add_argument("--split-stellar", action="store_true",
                    help="Vdisk,Vbulに別々のM/L(mu_d,mu_b)を持たせる")
    # chunked execution controls
    ap.add_argument("--chunk-size", type=int, default=0,
                    help="1回の実行で評価する(λ,A,gas)組み合わせ数の上限 (0で無制限)")
    ap.add_argument("--max-minutes", type=float, default=0.0,
                    help="壁時計時間の上限[分]。到達時に進捗を保存して終了 (0で無制限)")
    ap.add_argument("--progress-file", type=Path, default=None,
                    help="分割実行時の進捗ファイルパス (既定: --out に .progress.json を付加)")
    ap.add_argument("--reset-progress", action="store_true",
                    help="既存の進捗ファイルを無視し、新規に計算を開始する")
    args = ap.parse_args()
    # --ulm alias handling (does not override explicit --fdb-mode if user set it)
    if getattr(args, 'ulm', None) is not None:
        # Prefer explicit mapping only when default fdb_mode is unchanged
        # Volumetric (ULM-P) corresponds to model-based field; Surface (ULM-D) to interface/log kernel
        if getattr(args, 'fdb_mode', None) in (None, ''):
            setattr(args, 'fdb_mode', 'ulw' if args.ulm == 'p' else 'surface')
        else:
            # If both specified, --fdb-mode takes precedence; keep meta note
            pass

    names: List[str] = []
    if args.names_file and args.names_file.exists():
        for ln in args.names_file.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if ln and not ln.startswith("#"):
                names.append(ln)
    if args.names:
        names.extend(args.names)
    if not names:
        names = ["DDO154", "NGC2403", "NGC3198"]

    # Load geometry map if requested
    geo_map = {}
    if args.auto_geo or args.phys_defaults:
        gj = Path("data/imaging/geometry.json")
        if gj.exists():
            try:
                import json as _json

                geo_map = _json.loads(gj.read_text(encoding="utf-8"))
            except Exception:
                geo_map = {}

    # Load galaxies
    galaxies = []
    for nm in names:
        rc = read_sparc_massmodels(args.mrt, nm)
        g_obs, eg = to_accel(rc.R, rc.Vobs, rc.eV)
        # error floor: dV>=v_floor → eg_floor = 2*V*dV/R
        if args.err_floor_kms and args.err_floor_kms > 0:
            V = np.maximum(rc.Vobs, 1e-6)
            eg_floor = 2.0 * V * args.err_floor_kms / np.maximum(rc.R, 1e-6)
            eg = np.maximum(eg, eg_floor)
        if args.eg_frac_floor > 0.0 or args.eg_abs_floor > 0.0:
            eg = np.sqrt(eg * eg + (args.eg_frac_floor * g_obs) ** 2 + (args.eg_abs_floor ** 2))
        g_gas = rc.Vgas**2 / np.maximum(rc.R, 1e-6)
        g_disk = (rc.Vdisk**2) / np.maximum(rc.R, 1e-6)
        g_bul = (rc.Vbul**2) / np.maximum(rc.R, 1e-6)
        g_star = g_disk + g_bul
        # outer weighting mask
        thr = float(np.nanmax(rc.R)) * args.outer_frac
        w_outer = 1.0 + args.outer_weight * (rc.R >= thr)
        galaxies.append((nm, rc.R, rc.SBdisk, g_obs, eg, g_gas,
                         g_disk, g_bul, g_star, w_outer))

    # Baseline GR-only (per-galaxy mu)
    total_chi2_gr = 0.0
    N_gr = 0
    mus_gr: Dict[str, Dict[str, float]] = {}
    for nm, R, SB, g_obs, eg, g_gas, g_disk, g_bul, g_star, w_outer in galaxies:
        if args.split_stellar:
            # solve 2x2 weighted least squares for mu_d, mu_b (gas fixed)
            x1, x2 = g_disk, g_bul
            y = g_obs - g_gas
            w = (1.0 / np.maximum(eg, 1e-6)) * w_outer
            a11 = float(np.nansum(w * x1 * x1))
            a22 = float(np.nansum(w * x2 * x2))
            a12 = float(np.nansum(w * x1 * x2))
            b1 = float(np.nansum(w * x1 * y))
            b2 = float(np.nansum(w * x2 * y))
            det = a11 * a22 - a12 * a12 + 1e-12
            mu_d = max(min((b1 * a22 - b2 * a12) / det, args.mu_max), args.mu_min)
            mu_b = max(min((b2 * a11 - b1 * a12) / det, args.mu_max), args.mu_min)
            g_model = g_gas + mu_d * g_disk + mu_b * g_bul
            mus_gr[nm] = {"mu_d": mu_d, "mu_b": mu_b}
        else:
            mu = fit_mu_linear(g_obs, eg, g_gas, g_star, 0.0 * g_obs)
            mu = max(min(mu, args.mu_max), args.mu_min)
            g_model = g_gas + mu * g_star
            mus_gr[nm] = {"mu": mu}
        total_chi2_gr += chi2(g_obs, eg, g_model)
        N_gr += count_points(g_obs, eg, g_model)

    # Global grid search for (lam, A); per-galaxy mu solved
    gas_grid = [float(x) for x in args.gas_scale_grid.split(',') if x]
    lam_list = [float(x) for x in args.lam_grid.split(',') if x]
    A_list = [float(x) for x in args.A_grid.split(',') if x]
    combos_per_lam = len(A_list) * len(gas_grid)
    total_combos = len(lam_list) * combos_per_lam

    progress_path = args.progress_file or _default_progress_path(args.out)
    use_progress = progress_path.exists() or args.chunk_size > 0 or args.max_minutes > 0
    if args.reset_progress and progress_path.exists():
        progress_path.unlink()
    start_idx = 0
    progress_best: Dict | None = None
    progress_complete = False
    if use_progress:
        start_idx, progress_best, progress_complete = _load_progress(
            progress_path, names, lam_list, A_list, gas_grid, args.split_stellar
        )

    best_total = float('inf')
    best_combo = {'lam': float('nan'), 'A': float('nan'), 'gas_scale': float('nan')}
    best_mus: Dict[str, Dict[str, float]] = {}
    if progress_best:
        try:
            best_total = float(progress_best.get('chi2', float('inf')))
        except Exception:
            best_total = float('inf')
        best_combo = {
            'lam': float(progress_best.get('lam', float('nan'))),
            'A': float(progress_best.get('A', float('nan'))),
            'gas_scale': float(progress_best.get('gas_scale', float('nan'))),
        }
        best_mus = _jsonify_mus(progress_best.get('mus') or {})

    chunk_limit = max(int(args.chunk_size or 0), 0)
    max_seconds = max(float(args.max_minutes or 0.0), 0.0) * 60.0
    processed_this_run = 0
    last_idx = start_idx
    start_time = time.monotonic()
    finished = progress_complete and start_idx >= total_combos

    if total_combos == 0:
        finished = True
        last_idx = 0

    if (not finished) and total_combos > 0:
        break_requested = False
        for lam_idx, lam in enumerate(lam_list):
            lam_block_start = lam_idx * combos_per_lam
            lam_block_end = lam_block_start + combos_per_lam
            if lam_block_end <= start_idx:
                continue
            if lam_block_start >= total_combos or break_requested:
                break
            pre_ulw = _precompute_ulw_for_lambda(lam, args, galaxies, geo_map)
            for A_idx, A in enumerate(A_list):
                if break_requested:
                    break
                for g_idx, gscale in enumerate(gas_grid):
                    combo_idx = lam_block_start + A_idx * len(gas_grid) + g_idx
                    if combo_idx < start_idx:
                        continue
                    if chunk_limit and processed_this_run >= chunk_limit:
                        break_requested = True
                        break
                    elapsed = time.monotonic() - start_time
                    if max_seconds > 0.0 and processed_this_run > 0 and elapsed >= max_seconds:
                        break_requested = True
                        break
                    total_val, cur_mus = _evaluate_combo(
                        lam, A, gscale, pre_ulw, galaxies, mus_gr, args
                    )
                    processed_this_run += 1
                    last_idx = combo_idx + 1
                    if total_val < best_total:
                        best_total = total_val
                        best_combo = {'lam': float(lam), 'A': float(A), 'gas_scale': float(gscale)}
                        best_mus = _jsonify_mus(cur_mus)
                if break_requested:
                    break
        # if we exited loop due to limit, last_idx marks progress
    else:
        last_idx = max(last_idx, total_combos)

    next_idx = min(last_idx, total_combos)
    complete = (next_idx >= total_combos) if total_combos > 0 else True

    if not np.isfinite(best_total):
        raise SystemExit('no grid combination evaluated; verify dataset and parameter grids')

    lam_b = float(best_combo.get('lam', float('nan')))
    A_b = float(best_combo.get('A', float('nan')))
    gscale_b = float(best_combo.get('gas_scale', float('nan')))
    if not (np.isfinite(lam_b) and np.isfinite(A_b) and np.isfinite(gscale_b)):
        raise SystemExit('best combination undefined; progress data may be corrupted')
    total_chi2_ulw = float(best_total)
    # μ(k) 共有パラメータ（暫定推定: lam,Aに整合する格子点を選択）
    try:
        mu_eps_list = [float(x) for x in (args.mu_eps_grid.split(',') if isinstance(args.mu_eps_grid, str) else args.mu_eps_grid)]
        mu_k0_list = [float(x) for x in (args.mu_k0_grid.split(',') if isinstance(args.mu_k0_grid, str) else args.mu_k0_grid)]
        mu_m_list  = [float(x) for x in (args.mu_m_grid.split(',') if isinstance(args.mu_m_grid, str) else args.mu_m_grid)]
    except Exception:
        mu_eps_list, mu_k0_list, mu_m_list = [0.3], [0.1], [2.0]
    # 目安: k0 ≈ 1/λ, ε は A に単調対応とみなし A に近い格子を選ぶ
    def _nearest(arr, val):
        return min(arr, key=lambda z: abs(float(z) - float(val))) if arr else val
    k0_b = _nearest(mu_k0_list, (1.0 / max(lam_b, 1e-6)) if lam_b == lam_b else mu_k0_list[0])
    eps_b = _nearest(mu_eps_list, A_b if A_b == A_b else mu_eps_list[0])
    m_b   = _nearest(mu_m_list, 2.0)

    mu_k_best = {'eps': float(eps_b), 'k0': float(k0_b), 'm': float(m_b), 'shared': True}
    best_state_payload = {
        'chi2': float(best_total),
        'lam': float(lam_b),
        'A': float(A_b),
        'gas_scale': float(gscale_b),
        'mus': _jsonify_mus(best_mus),
        'mu_k': mu_k_best,
    }

    if not complete:
        if use_progress:
            _save_progress(
                progress_path, names, lam_list, A_list, gas_grid,
                args.split_stellar, next_idx, best_state_payload,
                total_combos, False,
            )
            print(f"[progress] saved to {progress_path} ({next_idx}/{total_combos} combos)")
        else:
            print('[progress] limit reached but no progress file requested; skipping save')
        print('chunk/time limit reached; re-run compare_fit_multi to continue from saved state.')
        return 0

    # Recompute N for AIC counting on best ULW
    best_pre_ulw = _precompute_ulw_for_lambda(lam_b, args, galaxies, geo_map)
    N_ulw = 0
    for (nm, R, SB, g_obs, eg, g_gas, g_disk, g_bul, g_star, w_outer), g_ulw_1 in zip(galaxies, best_pre_ulw):
        g_ulw = A_b * g_ulw_1
        if args is not None:
            try:
                from core.fdb_kernel import g_of_r as _gofr
                fac = 1.0 - 0.5 * float(getattr(args, 'aniso_lambda', 0.0) or 0.0) * _gofr(R, float(getattr(args, 'aniso_ell0_kpc', 0.0) or 0.0), int(getattr(args, 'aniso_m', 2) or 2))
                g_ulw = g_ulw * fac
            except Exception:
                pass
        gg = gscale_b * g_gas
        if args.split_stellar:
            mu_rec = best_mus.get(nm) or {}
            mu_d = float(mu_rec.get("mu_d", mus_gr.get(nm, {}).get("mu_d", 0.7)))
            mu_b = float(mu_rec.get("mu_b", mus_gr.get(nm, {}).get("mu_b", 0.7)))
            g_model = gg + mu_d * g_disk + mu_b * g_bul + g_ulw
        else:
            mu_rec = best_mus.get(nm) or {}
            mu = float(mu_rec.get("mu", mus_gr.get(nm, {}).get("mu", 0.7)))
            g_model = gg + mu * g_star + g_ulw
        N_ulw += count_points(g_obs, eg, g_model)

    if use_progress:
        _save_progress(
            progress_path, names, lam_list, A_list, gas_grid,
            args.split_stellar, total_combos, best_state_payload,
            total_combos, True,
        )
        print(f"[progress] completed; saved final state to {progress_path}")

    # AIC: -2logL ~ chi2_w なので AIC = chi2 + 2k とする
    k_gr = (2 if args.split_stellar else 1) * len(galaxies)
    k_ulw = k_gr + 3  # (lam,A,gas_scale) ※α_lineは廃止
    aic_gr = total_chi2_gr + 2 * k_gr
    aic_ulw = total_chi2_ulw + 2 * k_ulw

    # Report
    print("Galaxies:", ", ".join(names))
    print(f"GR-only total chi2={total_chi2_gr:.3g}")
    print(f"ULW best: lam={lam_b:.3g} kpc, A={A_b:.3g}, gas_scale={gscale_b:.3g}, total chi2={total_chi2_ulw:.3g}")
    for nm in names:
        mu_gr_s = mus_gr.get(nm, {})
        mu_ulw_s = best_mus.get(nm, {})
        if "mu" in mu_gr_s:
            gr_txt = f"mu={mu_gr_s['mu']:.3g}"
        else:
            gr_txt = f"mu_d={mu_gr_s.get('mu_d', float('nan')):.3g}, mu_b={mu_gr_s.get('mu_b', float('nan')):.3g}"
        if "mu" in mu_ulw_s:
            if "alpha_line" in mu_ulw_s:
                ulw_txt = f"mu={mu_ulw_s['mu']:.3g}, alpha_line={mu_ulw_s['alpha_line']:.3g}"
            else:
                ulw_txt = f"mu={mu_ulw_s['mu']:.3g}"
        else:
            extra = f", alpha_line={mu_ulw_s.get('alpha_line', float('nan')):.3g}" if "alpha_line" in mu_ulw_s else ""
            ulw_txt = f"mu_d={mu_ulw_s.get('mu_d', float('nan')):.3g}, mu_b={mu_ulw_s.get('mu_b', float('nan')):.3g}{extra}"
        print(f"  {nm}: GR({gr_txt}), ULW({ulw_txt})")

    # Build ML_star mapping (ASCII-safe) alongside legacy 'mu'
    def to_mlstar_map(mus: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        res: Dict[str, Dict[str, float]] = {}
        for nm, m in mus.items():
            if 'mu' in m:
                res[nm] = {'ML_star': float(m['mu'])}
            else:
                d = {}
                if 'mu_d' in m: d['ML_star_disk'] = float(m['mu_d'])
                if 'mu_b' in m: d['ML_star_bulge'] = float(m['mu_b'])
                res[nm] = d
        return res

    out = {
        "names": names,
        "pix_kpc": args.pix,
        "size": args.size,
        "boost": args.boost,
        "boost_tie_lam": bool(args.boost_tie_lam),
        "lam": lam_b,
        "A": A_b,
        "gas_scale": gscale_b,
        "chi2_total": {"GR": total_chi2_gr, "ULW": total_chi2_ulw},
        "N_total": {"GR": N_gr, "ULW": N_ulw},
        "AIC": {"GR": aic_gr, "ULW": aic_ulw, "k": {"GR": k_gr, "ULW": k_ulw}},
        "mu_k": mu_k_best,
        "mu": {"GR": mus_gr, "ULW": best_mus},
        "ML_star": {"GR": to_mlstar_map(mus_gr), "ULW": to_mlstar_map(best_mus)},
        "_aliases": {"note": "mu* keys deprecated; use ML_star* (ASCII) going forward"},
        "meta": {"fdb_mode": args.fdb_mode, "beta_forward": float(args.beta_forward)},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"saved: {args.out}")
    # Write artifact with run context for reproducibility
    try:
        from scripts.artifacts import write_artifact
        payload = {
            "command": "compare_fit_multi",
            "args": {
                k: getattr(args, k) for k in [
                    "pix", "size", "boost", "boost_tie_lam", "plane_alpha",
                    "bar_alpha", "irr_alpha", "aniso_q", "nl_gamma", "pad_factor",
                    "inv1_kind", "inv1_orth", "line_eps", "eg_frac_floor",
                    "eg_abs_floor", "err_floor_kms", "lam_grid", "A_grid",
                    "mu_eps_grid", "mu_k0_grid", "mu_m_grid", "mix_lam_ratio", "mix_w",
                ] if hasattr(args, k)
            },
            "selected": {
                "lam": lam_b, "A": A_b, "gas_scale": gscale_b,
                "k": {"GR": k_gr, "ULW": k_ulw},
            },
            "dataset": {
                "names": names,
                "mrt": str(args.mrt),
                "names_file": str(args.names_file) if args.names_file else None,
                "blacklist": "data/sparc/sets/blacklist.txt",
            },
            "metrics": {
                "chi2_total": {"GR": total_chi2_gr, "ULW": total_chi2_ulw},
                "AIC": {"GR": aic_gr, "ULW": aic_ulw},
                "N_total": {"GR": N_gr, "ULW": N_ulw},
            },
            "out_json": str(args.out),
            "ts_end": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        art = write_artifact("multi_fit", payload)
        print("artifact:", art)
    except Exception as e:
        print("warn: failed to write artifact:", e)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
