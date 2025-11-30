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
    alpha, eps, ml_scale, beta, R_ev_scale, sigma_ev_scale, v0 = vec
    if eps <= 0 or ml_scale <= 0 or beta < 0:
        return 1e30
    mask = data.R_kpc > r_cut
    if not np.any(mask):
        return 1e30
    R_eval = data.R_kpc[mask]
    Vobs = data.Vobs[mask]
    eV = data.eVobs[mask]
    # Newton from rotmod velocities if present
    V_newton = np.sqrt(
        np.clip(
            data.Vdisk_rotmod**2 + data.Vgas_rotmod**2 + data.Vbul_rotmod**2,
            0,
            None,
        )
    )
    V_newton = V_newton[mask]

    params = {
        "alpha": alpha,
        "eps": eps,
        "R_ev": R_ev_scale * params_global["R_d"],
        "sigma_ev": sigma_ev_scale * params_global["R_d"],
    }
    V_fdb = model_velocity(
        R_eval,
        R_grid,
        Sigma_env_grid,
        params,
    )
    V_tot = np.sqrt(np.clip(V_newton**2 + V_fdb**2 + v0**2, 0, None))
    err = np.sqrt(eV**2 + sigma_model**2)
    chi = (Vobs - V_tot) / err
    return float(np.sum(chi**2))


def fit_fdb_for_galaxy(csv_path: str):
    data = load_sparc_csv(csv_path)
    R_grid, Sigma_star_grid, Sigma_gas_grid = build_radial_grid(data)
    R_d = estimate_Rd(data)
    params_global["R_d"] = R_d

    # If rotmod velocities are present, build a Newton curve from them for sanity
    df_full = pd.read_csv(csv_path)
    has_rot = set(["Vgas_rotmod", "Vdisk_rotmod"]) <= set(df_full.columns)
    if has_rot:
        v_newton_rot = np.sqrt(np.clip(df_full["Vgas_rotmod"].to_numpy()**2 + df_full["Vdisk_rotmod"].to_numpy()**2, 0, None))
    else:
        v_newton_rot = None

    # Newton-only sanity check
    Sigma_env_grid_base = Sigma_gas_grid + 0.2 * Sigma_star_grid  # beta=0.2 trial
    chi2_newton = chi2_model(
        np.array([0.0, 0.1, 1.0, 0.2, 2.5, 0.7, 0.0]),
        data,
        R_grid,
        Sigma_env_grid_base,
    )
    print(f"Newton-only chi2 (alpha=0, eps=0.1, ml=1, beta=0.2): {chi2_newton:.3e}")

    # Fit outer radii only
    r_cut = 2.5 * R_d  # focus on outer disk
    sigma_model = 7.0  # km/s added in quadrature
    x0 = np.array([0.3, 0.1, 0.9, 0.2, 2.5, 0.7, 0.0])  # alpha, eps, ml_scale, beta, R_ev/Rd, sigma_ev/Rd, v0
    bounds = [
        (-1, 2),        # alpha
        (0.05, 0.6),    # eps [kpc]
        (0.6, 1.2),     # ml_scale
        (0.0, 0.3),     # beta
        (2.0, 3.0),     # R_ev / R_d
        (0.5, 1.0),     # sigma_ev / R_d
        (0.0, 50.0),    # v0 [km/s]
    ]

    res = minimize(
        lambda x: chi2_model(x, data, R_grid, Sigma_gas_grid + x[3] * Sigma_star_grid, r_cut=r_cut, sigma_model=sigma_model),
        x0,
        method="L-BFGS-B",
        bounds=bounds,
    )
    best = res.x
    print("Best-fit params [alpha, eps[kpc], ML_scale, beta, R_ev/Rd, sigma_ev/Rd, v0(km/s)]:", best)
    print(f"chi2 (r>{r_cut:.2f} kpc, sigma_model={sigma_model} km/s) = {res.fun:.3e}")

    Sigma_env_best = Sigma_gas_grid + best[3] * Sigma_star_grid
    V_fdb = model_velocity(
        data.R_kpc,
        R_grid,
        Sigma_env_best,
        {
            "alpha": best[0],
            "eps": best[1],
            "R_ev": best[4] * R_d,
            "sigma_ev": best[5] * R_d,
        },
    )

    # Optional Newton from rotmod velocities
    if v_newton_rot is not None:
        v_newton_use = v_newton_rot
    else:
        v_newton_use = model_velocity(
            data.R_kpc,
            R_grid,
            Sigma_env_best,
            {"alpha": 0.0, "eps": best[1], "R_ev": params_global["R_ev"], "sigma_ev": params_global["sigma_ev"]},
        )

    delta_v2 = np.clip(V_fdb**2, 0, None)
    V_tot = np.sqrt(np.clip(v_newton_use**2 + delta_v2, 0, None))

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
    out.to_csv("fdb_fit_output.csv", index=False)
    print("Saved fdb_fit_output.csv")

    # Residual plot (using V_tot)
    fig, ax = plt.subplots(2, 1, figsize=(6, 6), sharex=True)
    ax[0].errorbar(data.R_kpc, data.Vobs, yerr=data.eVobs, fmt="o", ms=3, label="Vobs")
    ax[0].plot(data.R_kpc, v_newton_use, label="Newton (rotmod or Σ)")
    ax[0].plot(data.R_kpc, V_tot, label="FDB total")
    ax[0].axvline(4.0, color="k", ls="--", alpha=0.3, label="r_cut=4 kpc")
    ax[0].set_ylabel("V [km/s]")
    ax[0].legend()
    resid = data.Vobs - V_tot
    ax[1].hlines(0, xmin=np.min(data.R_kpc), xmax=np.max(data.R_kpc), color="k", lw=0.5)
    ax[1].errorbar(data.R_kpc, resid, yerr=data.eVobs, fmt="o", ms=3)
    ax[1].set_xlabel("R [kpc]")
    ax[1].set_ylabel("Residual (Vobs - V_tot)")
    out_png = "fdb_residuals.png"
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    print(f"Saved {out_png}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: fdb_fit.py <sparc_csv>")
        sys.exit(1)

    fit_fdb_for_galaxy(sys.argv[1])
