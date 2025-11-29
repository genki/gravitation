#!/usr/bin/env python3
"""
FDB rotation-curve fit for a single SPARC galaxy (e.g., NGC 2403 / 3198).

Updates in this version:
- sanity: Newton-only check
- simplified 1-scale kernel (alpha, lambda, eps) with optional M/L scaling
- outer-radius-only fit (r > r_cut) and model noise added in quadrature
- optional Newton curve from rotmod Vdisk+Vgas columns
- residual plots for quick diagnosis

Input CSV columns (from convert_rotmod_to_csv.py):
R_kpc, Vobs, eVobs, Vgas_rotmod, Vdisk_rotmod,
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


@dataclass
class GalaxyData:
    R_kpc: np.ndarray
    Vobs: np.ndarray
    eVobs: np.ndarray
    Sigma_star: np.ndarray
    Sigma_gas: np.ndarray


def load_sparc_csv(path: str) -> GalaxyData:
    df = pd.read_csv(path)
    return GalaxyData(
        R_kpc=df["R_kpc"].to_numpy(),
        Vobs=df["Vobs"].to_numpy(),
        eVobs=df["eVobs"].to_numpy(),
        Sigma_star=df["Sigma_star"].to_numpy(),
        Sigma_gas=df["Sigma_gas"].to_numpy(),
    )


def build_radial_grid(data: GalaxyData, n_grid: int = 200) -> Tuple[np.ndarray, np.ndarray]:
    R_min = np.min(data.R_kpc) * 0.5
    R_max = np.max(data.R_kpc) * 1.2
    R_grid = np.linspace(R_min, R_max, n_grid)
    Sigma_star_grid = np.interp(R_grid, data.R_kpc, data.Sigma_star)
    Sigma_gas_grid = np.interp(R_grid, data.R_kpc, data.Sigma_gas)
    Sigma_tot = Sigma_star_grid + Sigma_gas_grid
    return R_grid, Sigma_tot


def softened_kernel_accel(
    R_eval: np.ndarray,
    R_grid: np.ndarray,
    Sigma_grid_pc2: np.ndarray,
    alpha: float = 0.0,
    lamb: float = 1.0,
    eps: float = 0.1,
    ml_scale: float = 1.0,
) -> np.ndarray:
    """Simplified kernel: softened 1/r × (1 + alpha exp(-|d|/lambda))."""
    Sigma_kpc2 = Sigma_grid_pc2 * 1e6 * ml_scale
    dR = np.gradient(R_grid)
    M_ring = 2.0 * np.pi * R_grid * Sigma_kpc2 * dR  # [Msun]

    a_R = np.zeros_like(R_eval)
    for i, R in enumerate(R_eval):
        d = R - R_grid
        denom = (d**2 + eps**2) ** 1.5
        base = d / denom  # ∂/∂R of softened 1/r
        dist = np.abs(d)
        yuk = 1.0 + alpha * np.exp(-dist / lamb)
        contrib = -G * M_ring * base * yuk  # [(km/s)^2 / kpc]
        a_R[i] = np.sum(contrib)
    return a_R


def model_velocity(
    R_eval: np.ndarray,
    R_grid: np.ndarray,
    Sigma_grid: np.ndarray,
    params: Dict[str, float],
) -> np.ndarray:
    a_R = softened_kernel_accel(
        R_eval,
        R_grid,
        Sigma_grid,
        alpha=params["alpha"],
        lamb=params["lambda"],
        eps=params["eps"],
        ml_scale=params["ml_scale"],
    )
    v2 = R_eval * np.abs(a_R)
    return np.sqrt(np.clip(v2, 0.0, None))


def chi2_model(
    vec: np.ndarray,
    data: GalaxyData,
    R_grid: np.ndarray,
    Sigma_grid: np.ndarray,
    r_cut: float = 0.0,
    sigma_model: float = 0.0,
) -> float:
    alpha, lamb, eps, ml_scale = vec
    if lamb <= 0 or eps <= 0 or ml_scale <= 0:
        return 1e30
    mask = data.R_kpc > r_cut
    if not np.any(mask):
        return 1e30
    R_eval = data.R_kpc[mask]
    Vobs = data.Vobs[mask]
    eV = data.eVobs[mask]
    V_model = model_velocity(
        R_eval,
        R_grid,
        Sigma_grid,
        {"alpha": alpha, "lambda": lamb, "eps": eps, "ml_scale": ml_scale},
    )
    err = np.sqrt(eV**2 + sigma_model**2)
    chi = (Vobs - V_model) / err
    return float(np.sum(chi**2))


def fit_fdb_for_galaxy(csv_path: str):
    data = load_sparc_csv(csv_path)
    R_grid, Sigma_grid = build_radial_grid(data)

    # If rotmod velocities are present, build a Newton curve from them for sanity
    df_full = pd.read_csv(csv_path)
    has_rot = set(["Vgas_rotmod", "Vdisk_rotmod"]) <= set(df_full.columns)
    if has_rot:
        v_newton_rot = np.sqrt(np.clip(df_full["Vgas_rotmod"].to_numpy()**2 + df_full["Vdisk_rotmod"].to_numpy()**2, 0, None))
    else:
        v_newton_rot = None

    # Newton-only sanity check
    chi2_newton = chi2_model(np.array([0.0, 1.0, 0.1, 1.0]), data, R_grid, Sigma_grid)
    print(f"Newton-only chi2 (alpha=0, eps=0.1, ml=1): {chi2_newton:.3e}")

    # Fit outer radii only
    r_cut = 4.0  # kpc
    sigma_model = 5.0  # km/s added in quadrature
    x0 = np.array([0.2, 5.0, 0.1, 0.8])  # alpha, lambda[kpc], eps[kpc], ml_scale
    bounds = [(-2, 2), (0.5, 50), (0.05, 1.0), (0.3, 1.5)]

    res = minimize(
        lambda x: chi2_model(x, data, R_grid, Sigma_grid, r_cut=r_cut, sigma_model=sigma_model),
        x0,
        method="L-BFGS-B",
        bounds=bounds,
    )
    best = res.x
    print("Best-fit params [alpha, lambda[kpc], eps[kpc], ML_scale]:", best)
    print(f"chi2 (r>{r_cut} kpc, sigma_model={sigma_model} km/s) = {res.fun:.3e}")

    V_fdb = model_velocity(
        data.R_kpc,
        R_grid,
        Sigma_grid,
        {"alpha": best[0], "lambda": best[1], "eps": best[2], "ml_scale": best[3]},
    )

    # Optional Newton from rotmod velocities
    if v_newton_rot is not None:
        v_newton_use = v_newton_rot
    else:
        v_newton_use = model_velocity(
            data.R_kpc,
            R_grid,
            Sigma_grid,
            {"alpha": 0.0, "lambda": 1.0, "eps": 0.1, "ml_scale": 1.0},
        )

    out = pd.DataFrame(
        {
            "R_kpc": data.R_kpc,
            "Vobs": data.Vobs,
            "eVobs": data.eVobs,
            "V_FDB": V_fdb,
            "V_Newton": v_newton_use,
        }
    )
    out.to_csv("fdb_fit_output.csv", index=False)
    print("Saved fdb_fit_output.csv")

    # Residual plot
    fig, ax = plt.subplots(2, 1, figsize=(6, 6), sharex=True)
    ax[0].errorbar(data.R_kpc, data.Vobs, yerr=data.eVobs, fmt="o", ms=3, label="Vobs")
    ax[0].plot(data.R_kpc, v_newton_use, label="Newton (rotmod or Σ)")
    ax[0].plot(data.R_kpc, V_fdb, label="FDB model")
    ax[0].axvline(4.0, color="k", ls="--", alpha=0.3, label="r_cut=4 kpc")
    ax[0].set_ylabel("V [km/s]")
    ax[0].legend()
    resid = data.Vobs - V_fdb
    ax[1].hlines(0, xmin=np.min(data.R_kpc), xmax=np.max(data.R_kpc), color="k", lw=0.5)
    ax[1].errorbar(data.R_kpc, resid, yerr=data.eVobs, fmt="o", ms=3)
    ax[1].set_xlabel("R [kpc]")
    ax[1].set_ylabel("Residual (Vobs - V_FDB)")
    out_png = "fdb_residuals.png"
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    print(f"Saved {out_png}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: fdb_fit.py <sparc_csv>")
        sys.exit(1)

    fit_fdb_for_galaxy(sys.argv[1])
