#!/usr/bin/env python3
"""
FDB rotation-curve fit for a single SPARC galaxy (e.g., NGC 2403 / 3198).

This version implements:
- Newton-only sanity using rotmod Vdisk/Vgas/Vbul when present.
- Shell-weighted FDB kernel acting on gas-prior surface density \(\Sigma_{\rm env}=\Sigma_{\rm gas}+\beta\Sigma_\star\).
- Δv² add-on: \(v_{\rm tot}^2 = v_{\rm Newt}^2 + \Delta v_{\rm FDB}^2\).
- Outer-only fit (r > 2 R_d) with model noise in quadrature.
- Residual plot saved per run.

Input CSV columns (from convert_rotmod_to_csv.py):
R_kpc, Vobs, eVobs, Vgas_rotmod, Vdisk_rotmod, Vbul_rotmod,
Sigma_star (Msun/pc^2), Sigma_gas (Msun/pc^2)
"""

import sys
import os
from dataclasses import dataclass
from typing import Tuple, Dict

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# Gravitational constant in convenient units:
# G ≈ 4.30091e-6 kpc (km/s)^2 / Msun
G = 4.30091e-6  # [kpc (km/s)^2 Msun^{-1}]

# global parameters for shell location (set per galaxy)
params_global = {"R_ev": 5.0, "sigma_ev": 2.0}


@dataclass
class GalaxyData:
    R_kpc: np.ndarray
    Vobs: np.ndarray
    eVobs: np.ndarray
    Sigma_star: np.ndarray
    Sigma_gas: np.ndarray
    Vdisk_rotmod: np.ndarray
    Vgas_rotmod: np.ndarray
    Vbul_rotmod: np.ndarray


def load_sparc_csv(path: str) -> GalaxyData:
    df = pd.read_csv(path)
    return GalaxyData(
        R_kpc=df["R_kpc"].to_numpy(),
        Vobs=df["Vobs"].to_numpy(),
        eVobs=df["eVobs"].to_numpy(),
        Sigma_star=df["Sigma_star"].to_numpy(),
        Sigma_gas=df["Sigma_gas"].to_numpy(),
        Vdisk_rotmod=df.get("Vdisk_rotmod", pd.Series(np.zeros(len(df)))).to_numpy(),
        Vgas_rotmod=df.get("Vgas_rotmod", pd.Series(np.zeros(len(df)))).to_numpy(),
        Vbul_rotmod=df.get("Vbul_rotmod", pd.Series(np.zeros(len(df)))).to_numpy(),
    )


def build_radial_grid(data: GalaxyData, n_grid: int = 200) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    R_min = np.min(data.R_kpc) * 0.5
    R_max = np.max(data.R_kpc) * 1.2
    R_grid = np.linspace(R_min, R_max, n_grid)
    Sigma_star_grid = np.interp(R_grid, data.R_kpc, data.Sigma_star)
    Sigma_gas_grid = np.interp(R_grid, data.R_kpc, data.Sigma_gas)
    return R_grid, Sigma_star_grid, Sigma_gas_grid


def estimate_shell_from_sigma(R: np.ndarray, Sigma_gas: np.ndarray) -> Tuple[float, float]:
    """
    Crude estimate of the radius where the gas surface density drops most steeply
    (interpreted as the center of the evanescent layer), and an associated width.

    Returns
    -------
    R_ev_est : float
        Estimated shell center [kpc].
    sigma_R_ev : float
        Estimated 1-sigma width [kpc].
    """
    R = np.asarray(R)
    Sig = np.asarray(Sigma_gas)
    mask = np.isfinite(R) & np.isfinite(Sig) & (Sig > 0)
    if mask.sum() < 4:
        # Fallback: use median radius with wide uncertainty
        R_med = np.median(R[mask]) if mask.any() else np.median(R)
        return float(R_med), float(0.5 * R_med)
    Rm = R[mask]
    Sm = Sig[mask]
    # simple smoothing to suppress noise
    Sm_smooth = pd.Series(Sm).rolling(window=3, center=True, min_periods=1).mean().to_numpy()
    dS = np.gradient(Sm_smooth, Rm)
    idx = int(np.argmin(dS))  # most negative slope
    R_ev_est = float(Rm[idx])
    # width: region where slope is steeper than half the minimum (more negative)
    thresh = 0.5 * dS[idx]
    left = idx
    while left > 0 and dS[left] <= thresh:
        left -= 1
    right = idx
    while right < len(Rm) - 1 and dS[right] <= thresh:
        right += 1
    sigma_R = 0.5 * (Rm[right] - Rm[left]) if right > left else 0.3 * R_ev_est
    return R_ev_est, float(abs(sigma_R))


def estimate_Rd(data: GalaxyData) -> float:
    """
    Rough exponential scale length from Sigma_star (proxy for SBdisk).
    """
    mask = data.Sigma_star > np.max(data.Sigma_star) * 1e-3
    R = data.R_kpc[mask]
    Sig = data.Sigma_star[mask]
    if len(R) < 5:
        return np.median(data.R_kpc)
    coeffs = np.polyfit(R, np.log(np.clip(Sig, 1e-12, None)), 1)
    slope = coeffs[0]
    if slope >= 0:
        return np.median(data.R_kpc)
    return -1.0 / slope


def softened_kernel_accel(
    R_eval: np.ndarray,
    R_grid: np.ndarray,
    Sigma_env_pc2: np.ndarray,
    alpha: float,
    eps: float,
    R_ev: float,
    sigma_ev: float,
) -> np.ndarray:
    """
    Shell-weighted kernel: softened 1/r multiplied by [1 + alpha * shell(R')].
    shell(R') = exp(-(R'-R_ev)^2/(2 sigma_ev^2)).
    """
    Sigma_kpc2 = Sigma_env_pc2 * 1e6
    shell = np.exp(-((R_grid - R_ev) ** 2) / (2.0 * sigma_ev**2))
    dR = np.gradient(R_grid)
    M_ring = 2.0 * np.pi * R_grid * Sigma_kpc2 * dR  # [Msun]

    a_R = np.zeros_like(R_eval)
    for i, R in enumerate(R_eval):
        d = R - R_grid
        denom = (d**2 + eps**2) ** 1.5
        base = d / denom  # ∂/∂R of softened 1/r
        weight = 1.0 + alpha * shell
        contrib = -G * M_ring * base * weight  # [(km/s)^2 / kpc]
        a_R[i] = np.sum(contrib)
    return a_R


def model_velocity(
    R_eval: np.ndarray,
    R_grid: np.ndarray,
    Sigma_env: np.ndarray,
    params: Dict[str, float],
) -> np.ndarray:
    a_R = softened_kernel_accel(
        R_eval,
        R_grid,
        Sigma_env,
        alpha=params["alpha"],
        eps=params["eps"],
        R_ev=params["R_ev"],
        sigma_ev=params["sigma_ev"],
    )
    v2 = R_eval * np.abs(a_R)
    return np.sqrt(np.clip(v2, 0.0, None))


def chi2_model(
    vec: np.ndarray,
    data: GalaxyData,
    R_grid: np.ndarray,
    Sigma_env_grid: np.ndarray,
    r_cut: float = 0.0,
    sigma_model: float = 0.0,
) -> float:
    # Interpret parameters as:
    #   alpha    -> Δv^2_FDB (constant FDB contribution to v^2, ≥0)
    #   ml_scale -> rescaling of Newtonian rotation curve
    #   beta, eps, v0 currently unused (kept for compatibility)
    alpha, eps, ml_scale, mu, R_ev_scale, sigma_ev_scale, v0 = vec
    if ml_scale <= 0:
        return 1e30
    mask = data.R_kpc > r_cut
    if not np.any(mask):
        return 1e30
    R_eval = data.R_kpc[mask]
    Vobs = data.Vobs[mask]
    eV = data.eVobs[mask]
    # Newtonian rotation curve from rotmod velocities
    V_newton = np.sqrt(
        np.clip(
            data.Vdisk_rotmod**2 + data.Vgas_rotmod**2 + data.Vbul_rotmod**2,
            0,
            None,
        )
    )
    V_newton = V_newton[mask]

    # Newton + 1/r geometry in v^2 space with competitive mixing:
    #   v_tot^2(R) = [A_N(R) * ml_scale * V_newton]^2 + A_F(R) * Δv^2_FDB
    #   A_N(R) = 1 - mu w(R),  A_F(R) = mu w(R)
    R_ev = R_ev_scale * params_global["R_d"]
    sigma_ev = sigma_ev_scale * params_global["R_d"]
    # Transition weight w(R): 0 (inner, Newton-dominated) -> 1 (outer, FDB-dominated).
    if sigma_ev > 0:
        w = 1.0 / (1.0 + np.exp(-(R_eval - R_ev) / sigma_ev))
    else:
        w = np.zeros_like(R_eval)
    mu = np.clip(mu, 0.0, 1.0)
    A_F = mu * w
    A_N = 1.0 - A_F
    delta_v2 = max(alpha, 0.0)
    v2_tot = (A_N * ml_scale * V_newton) ** 2 + A_F * delta_v2
    V_tot = np.sqrt(np.clip(v2_tot, 0, None))
    err = np.sqrt(eV**2 + sigma_model**2)
    chi = (Vobs - V_tot) / err
    chi2 = float(np.sum(chi**2))
    # Prior term: keep R_ev close to SPARC-based estimate with width sigma_R_ev
    R_ev_est = params_global.get("R_ev_est")
    sigma_R_ev = params_global.get("sigma_R_ev")
    if R_ev_est is not None and sigma_R_ev is not None and sigma_R_ev > 0:
        chi2 += ((R_ev - R_ev_est) / sigma_R_ev) ** 2
    return chi2


def fit_fdb_for_galaxy(csv_path: str):
    data = load_sparc_csv(csv_path)
    galaxy_tag = os.path.splitext(os.path.basename(csv_path))[0]
    R_grid, Sigma_star_grid, Sigma_gas_grid = build_radial_grid(data)
    R_d = estimate_Rd(data)
    params_global["R_d"] = R_d
    # Estimate shell center and its uncertainty from Σ_gas profile
    R_ev_est, sigma_R_ev = estimate_shell_from_sigma(data.R_kpc, data.Sigma_gas)
    params_global["R_ev_est"] = R_ev_est
    params_global["sigma_R_ev"] = sigma_R_ev

    # If rotmod velocities are present, build a Newton curve from them for sanity
    df_full = pd.read_csv(csv_path)
    has_rot = set(["Vgas_rotmod", "Vdisk_rotmod"]) <= set(df_full.columns)
    if has_rot:
        v_newton_rot = np.sqrt(np.clip(df_full["Vgas_rotmod"].to_numpy()**2 + df_full["Vdisk_rotmod"].to_numpy()**2, 0, None))
    else:
        v_newton_rot = None

    # Newton-only sanity check (ml_scale=1, Δv^2_FDB=0, mu=0)
    chi2_newton = chi2_model(
        np.array([0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0]),
        data,
        R_grid,
        Sigma_gas_grid,
    )
    print(f"Newton-only chi2 (ml_scale=1, Δv^2_FDB=0): {chi2_newton:.3e}")

    # Fit radii outside one disk scale length
    r_cut = 1.0 * R_d
    sigma_model = 8.0  # km/s added in quadrature
    # alpha(Δv^2_FDB), eps(unused), ml_scale, mu, R_ev/Rd, sigma_ev/Rd, v0(unused)
    x0 = np.array([500.0, 0.0, 0.9, 0.7, 2.5, 0.7, 0.0])
    bounds = [
        (0.0, 5e4),     # alpha = Δv^2_FDB
        (0.0, 0.0),     # eps (unused)
        (0.6, 1.0),     # ml_scale (do not exceed Newton)
        (0.3, 1.0),     # mu (ensure FDB does not vanish where w>0)
        (2.0, 3.0),     # R_ev / R_d
        (0.5, 1.0),     # sigma_ev / R_d
        (0.0, 0.0),     # v0 (unused)
    ]

    res = minimize(
        lambda x: chi2_model(x, data, R_grid, Sigma_gas_grid, r_cut=r_cut, sigma_model=sigma_model),
        x0,
        method="L-BFGS-B",
        bounds=bounds,
    )
    best = res.x
    print("Best-fit params [alpha, eps[kpc], ML_scale, beta, R_ev/Rd, sigma_ev/Rd, v0(km/s)]:", best)
    print(f"chi2 (r>{r_cut:.2f} kpc, sigma_model={sigma_model} km/s) = {res.fun:.3e}")

    # Newton curve from rotmod velocities
    if v_newton_rot is not None:
        v_newton_use = v_newton_rot
    else:
        v_newton_use = np.zeros_like(data.R_kpc)

    # Competitive mixing Newton + 1/r in v^2 space
    alpha, ml_scale, mu = best[0], best[2], best[3]
    R_ev = best[4] * R_d
    sigma_ev = best[5] * R_d
    R_all = data.R_kpc
    if sigma_ev > 0:
        w_all = 1.0 / (1.0 + np.exp(-(R_all - R_ev) / sigma_ev))
    else:
        w_all = np.zeros_like(R_all)
    mu = np.clip(mu, 0.0, 1.0)
    A_F_all = mu * w_all
    A_N_all = 1.0 - A_F_all
    delta_v2 = max(alpha, 0.0)
    v2_tot_all = (A_N_all * ml_scale * v_newton_use) ** 2 + A_F_all * delta_v2
    V_tot = np.sqrt(np.clip(v2_tot_all, 0, None))

    out = pd.DataFrame(
        {
            "R_kpc": data.R_kpc,
            "Vobs": data.Vobs,
            "eVobs": data.eVobs,
            "V_Newton": v_newton_use,
            "delta_v2_FDB": delta_v2,
            "V_tot": V_tot,
        }
    )
    # Write per-galaxy output into ./out
    os.makedirs("out", exist_ok=True)
    out_csv = os.path.join("out", f"{galaxy_tag}_fdb_fit_output.csv")
    out.to_csv(out_csv, index=False)
    print(f"Saved {out_csv}")

    # Combined summary plot per galaxy:
    #  - Top: rotation curve (Vobs, Newton, FDB total)
    #  - Bottom: normalized SPARC profiles vs R
    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(7, 6))

    # Top: rotation curves
    ax0.errorbar(
        data.R_kpc, data.Vobs, yerr=data.eVobs, fmt="o", ms=3, label="Vobs"
    )
    ax0.plot(data.R_kpc, v_newton_use, label="Newton (rotmod)")
    ax0.plot(data.R_kpc, V_tot, label="FDB total")
    ax0.set_ylabel("V [km/s]")
    ax0.legend()

    # Bottom: normalized SPARC per-radius quantities (0–1) vs R
    # Normalize each series by its own max to lie in [0,1].
    def norm_series(arr: np.ndarray) -> np.ndarray:
        m = np.nanmax(np.abs(arr))
        if m <= 0:
            return np.zeros_like(arr)
        return arr / m

    R = data.R_kpc
    # For gas, errors and velocities, normalize over all radii.
    series = {
        "errV": norm_series(data.eVobs),
        "Vgas": norm_series(data.Vgas_rotmod),
        "Vdisk": norm_series(data.Vdisk_rotmod),
        "Vbul": norm_series(data.Vbul_rotmod),
        r"$\Sigma_{\rm gas}$": norm_series(data.Sigma_gas),
    }
    # For stellar surface density, estimate max using only R > r_cut so that
    # the central peak does not dominate the normalization.
    star_vals = data.Sigma_star
    mask_outer = data.R_kpc > r_cut
    if np.any(mask_outer):
        m_star = np.nanmax(np.abs(star_vals[mask_outer]))
    else:
        m_star = np.nanmax(np.abs(star_vals))
    if m_star <= 0:
        star_norm = np.zeros_like(star_vals)
    else:
        star_norm = star_vals / m_star
    series["Sigma_star"] = star_norm
    for label, vals in series.items():
        ax1.plot(R, vals, label=label)
    ax1.set_xlabel("R [kpc]")
    ax1.set_ylabel("normalized (0–1)")
    ax1.set_ylim(0, 1.05)
    ax1.legend(fontsize=8, ncol=2)

    plt.tight_layout()
    summary_png = os.path.join("out", f"{galaxy_tag}_summary.png")
    plt.savefig(summary_png, dpi=150)
    print(f"Saved {summary_png}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: fdb_fit.py <sparc_csv>")
        sys.exit(1)

    fit_fdb_for_galaxy(sys.argv[1])
