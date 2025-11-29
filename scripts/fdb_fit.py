#!/usr/bin/env python3
"""
Simple FDB rotation curve fit for a single SPARC galaxy (e.g., NGC 2403 / 3198).

This is a *skeleton* script:
- assumes a CSV with columns: R_kpc, Vobs, eVobs, Sigma_star, Sigma_gas
- uses a minimal ring-sum FDB kernel as described in main.md §6.1
- fits (alpha1, lambda1, alpha2, lambda2) by chi^2 minimization

Adapt column names / units to your local SPARC files before use.
"""

import sys
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

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


def fdb_kernel_accel(
    R_eval: np.ndarray,
    R_grid: np.ndarray,
    Sigma_grid: np.ndarray,
    alpha1: float,
    lambda1: float,
    alpha2: float,
    lambda2: float,
    eps: float = 0.1,
) -> np.ndarray:
    """
    Compute radial acceleration a_R(R_eval) from the FDB kernel using ring summation.

    R_eval: radii where we want the acceleration [kpc]
    R_grid: ring mid-radii [kpc]
    Sigma_grid: total surface density at R_grid [Msun / kpc^2]
    eps: softening length [kpc]
    """
    dR = np.gradient(R_grid)
    M_ring = 2.0 * np.pi * R_grid * Sigma_grid * dR  # [Msun]

    a_R = np.zeros_like(R_eval)
    for i, R in enumerate(R_eval):
        d = R - R_grid
        denom = (d**2 + eps**2) ** 1.5
        base = d / denom  # ∂/∂R of softened 1/r
        dist = np.abs(d)
        yuk = (
            1.0
            + alpha1 * np.exp(-dist / lambda1)
            + alpha2 * np.exp(-dist / lambda2)
        )
        contrib = -G * M_ring * base * yuk  # [(km/s)^2 / kpc]
        a_R[i] = np.sum(contrib)

    return a_R  # [(km/s)^2 / kpc]


def fdb_velocity(
    R_eval: np.ndarray,
    R_grid: np.ndarray,
    Sigma_grid: np.ndarray,
    params: Tuple[float, float, float, float],
) -> np.ndarray:
    alpha1, lambda1, alpha2, lambda2 = params
    a_R = fdb_kernel_accel(R_eval, R_grid, Sigma_grid, alpha1, lambda1, alpha2, lambda2)
    v2 = R_eval * np.abs(a_R)
    v = np.sqrt(np.clip(v2, 0.0, None))
    return v  # [km/s]


def chi2_fdb(
    params: Tuple[float, float, float, float],
    data: GalaxyData,
    R_grid: np.ndarray,
    Sigma_grid: np.ndarray,
) -> float:
    alpha1, lambda1, alpha2, lambda2 = params
    if lambda1 <= 0 or lambda2 <= 0:
        return 1e30
    V_model = fdb_velocity(data.R_kpc, R_grid, Sigma_grid, params)
    chi = (data.Vobs - V_model) / data.eVobs
    return float(np.sum(chi**2))


def fit_fdb_for_galaxy(csv_path: str):
    data = load_sparc_csv(csv_path)
    R_grid, Sigma_grid = build_radial_grid(data)

    x0 = np.array([0.5, 3.0, 0.5, 10.0])  # alpha1, lambda1[kpc], alpha2, lambda2[kpc]

    res = minimize(lambda x: chi2_fdb(tuple(x), data, R_grid, Sigma_grid), x0, method="Nelder-Mead")
    best = res.x
    print("Best-fit FDB params:", best)
    print("chi2 =", res.fun)

    V_fdb = fdb_velocity(data.R_kpc, R_grid, Sigma_grid, tuple(best))

    out = pd.DataFrame(
        {
            "R_kpc": data.R_kpc,
            "Vobs": data.Vobs,
            "eVobs": data.eVobs,
            "V_FDB": V_fdb,
        }
    )
    out.to_csv("fdb_fit_output.csv", index=False)
    print("Saved fdb_fit_output.csv")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: fdb_fit.py <sparc_csv>")
        sys.exit(1)

    fit_fdb_for_galaxy(sys.argv[1])

