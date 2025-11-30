#!/usr/bin/env python3
"""
FDB rotation-curve fit (v2 kernel): Newton + 1/r^2 vs 1/r with offset applied
after constructing the Newtonian curve.

Model:
  v_tot^2(R) = v_Newt^2(R) * (1 - eps * W(R)) + Delta_v2 * W(R)

where:
  - v_Newt(R) is the rotmod Newtonian rotation curve (Vdisk, Vgas, Vbul).
  - W(R) is a smooth transition function:
        W(R) = 0.5 * [1 + tanh((R - R_t) / dR)]
    with R_t ~ transition radius (offset of the evanescent layer),
    dR ~ transition width.
  - eps (0 <= eps <= 0.5) controls how much Newtonian 1/r^2 is attenuated
    where the 1/r drift is active.
  - Delta_v2 >= 0 is the asymptotic v^2 contribution from the 1/r term.

This file fits NGC 2403 as a first v2 test case.
"""

import sys
import os
from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt


@dataclass
class GalaxyData:
    R_kpc: np.ndarray
    Vobs: np.ndarray
    eVobs: np.ndarray
    Vdisk: np.ndarray
    Vgas: np.ndarray
    Vbul: np.ndarray
    Sigma_gas: np.ndarray
    Sigma_star: np.ndarray


def load_sparc_csv(path: str) -> GalaxyData:
    df = pd.read_csv(path)
    return GalaxyData(
        R_kpc=df["R_kpc"].to_numpy(),
        Vobs=df["Vobs"].to_numpy(),
        eVobs=df["eVobs"].to_numpy(),
        Vdisk=df.get("Vdisk_rotmod", pd.Series(np.zeros(len(df)))).to_numpy(),
        Vgas=df.get("Vgas_rotmod", pd.Series(np.zeros(len(df)))).to_numpy(),
        Vbul=df.get("Vbul_rotmod", pd.Series(np.zeros(len(df)))).to_numpy(),
        Sigma_gas=df["Sigma_gas"].to_numpy(),
        Sigma_star=df["Sigma_star"].to_numpy(),
    )


def estimate_transition_radius(R: np.ndarray, Sigma_gas: np.ndarray) -> Tuple[float, float]:
    """
    Estimate the radius where Sigma_gas drops most steeply (transition center)
    and a width parameter from the extent of the steep region.
    """
    R = np.asarray(R)
    Sig = np.asarray(Sigma_gas)
    mask = np.isfinite(R) & np.isfinite(Sig) & (Sig > 0)
    if mask.sum() < 4:
        R_med = np.median(R[mask]) if mask.any() else np.median(R)
        return float(R_med), float(0.3 * R_med)
    Rm = R[mask]
    Sm = Sig[mask]
    Sm_smooth = pd.Series(Sm).rolling(window=3, center=True, min_periods=1).mean().to_numpy()
    dS = np.gradient(Sm_smooth, Rm)
    idx = int(np.argmin(dS))  # most negative slope
    R_t = float(Rm[idx])
    # width: region where slope is steeper than half the minimum
    thresh = 0.5 * dS[idx]
    left = idx
    while left > 0 and dS[left] <= thresh:
        left -= 1
    right = idx
    while right < len(Rm) - 1 and dS[right] <= thresh:
        right += 1
    dR = 0.5 * (Rm[right] - Rm[left]) if right > left else 0.3 * R_t
    return R_t, float(abs(dR))


def transition_weight(R: np.ndarray, R_t: float, dR: float) -> np.ndarray:
    if dR <= 0:
        return np.zeros_like(R)
    x = (R - R_t) / dR
    return 0.5 * (1.0 + np.tanh(x))


def chi2_v2(
    vec: np.ndarray,
    g: GalaxyData,
    R_t_prior: float,
    dR_prior: float,
    sigma_model: float = 8.0,
) -> float:
    """
    Parameter vector: [Delta_v2, eps, R_t, dR]
    """
    Delta_v2, eps, R_t, dR = vec
    if Delta_v2 < 0 or not (0.0 <= eps <= 0.5) or dR <= 0:
        return 1e30

    R = g.R_kpc
    Vobs = g.Vobs
    eV = g.eVobs
    Vn = np.sqrt(np.clip(g.Vdisk**2 + g.Vgas**2 + g.Vbul**2, 0, None))

    W = transition_weight(R, R_t, dR)
    # v_tot^2 = v_Newt^2 * (1 - eps W) + Delta_v2 W
    v2_tot = (1.0 - eps * W) * (Vn**2) + Delta_v2 * W
    V_tot = np.sqrt(np.clip(v2_tot, 0.0, None))

    err = np.sqrt(eV**2 + sigma_model**2)
    chi = (Vobs - V_tot) / err
    chi2 = float(np.sum(chi**2))

    # Prior to keep R_t and dR near gas-based estimates
    if dR_prior > 0:
        chi2 += ((R_t - R_t_prior) / dR_prior) ** 2
    return chi2


def fit_galaxy_v2(csv_path: str):
    g = load_sparc_csv(csv_path)
    galaxy_tag = os.path.splitext(os.path.basename(csv_path))[0].replace("_sparc", "")

    # Estimate transition radius from Sigma_gas
    R_t_est, dR_est = estimate_transition_radius(g.R_kpc, g.Sigma_gas)
    print(f"Estimated transition: R_t ≈ {R_t_est:.2f} kpc, dR ≈ {dR_est:.2f} kpc")

    # Initial guess: Delta_v2 from outer observed v^2, eps small, R_t~estimate, dR~estimate
    v_outer = np.median(g.Vobs[g.R_kpc > R_t_est])
    Delta0 = max(v_outer**2 - np.median((g.Vdisk[g.R_kpc > R_t_est]**2 +
                                         g.Vgas[g.R_kpc > R_t_est]**2 +
                                         g.Vbul[g.R_kpc > R_t_est]**2)), 0.0)
    x0 = np.array([Delta0, 0.2, R_t_est, dR_est])
    bounds = [
        (0.0, 5e4),         # Delta_v2
        (0.0, 0.5),         # eps
        (0.5 * R_t_est, 2.0 * R_t_est),  # R_t
        (0.2 * dR_est, 3.0 * dR_est),    # dR
    ]

    res = minimize(
        lambda x: chi2_v2(x, g, R_t_est, dR_est),
        x0,
        method="L-BFGS-B",
        bounds=bounds,
    )
    print("Best-fit v2 params [Delta_v2, eps, R_t, dR]:", res.x)
    print("chi2_v2 =", res.fun)

    # Build model curve
    Delta_v2, eps, R_t, dR = res.x
    R = g.R_kpc
    Vn = np.sqrt(np.clip(g.Vdisk**2 + g.Vgas**2 + g.Vbul**2, 0, None))
    W = transition_weight(R, R_t, dR)
    v2_tot = (1.0 - eps * W) * (Vn**2) + Delta_v2 * W
    V_tot = np.sqrt(np.clip(v2_tot, 0.0, None))

    # Plot
    os.makedirs("image", exist_ok=True)
    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(7, 6))

    ax0.errorbar(R, g.Vobs, yerr=g.eVobs, fmt="o", ms=3, label="Vobs")
    ax0.plot(R, Vn, label="Newton (rotmod)")
    ax0.plot(R, V_tot, label="FDB v2 total")
    ax0.set_ylabel("V [km/s]")
    ax0.legend()

    # Bottom: W(R) and Sigma_gas profile
    ax1.plot(R, W, label="W(R)")
    # normalize Sigma_gas for display
    if np.nanmax(g.Sigma_gas) > 0:
        ax1.plot(R, g.Sigma_gas / np.nanmax(g.Sigma_gas), label="Sigma_gas (norm)")
    ax1.axvline(R_t, color="k", ls="--", alpha=0.5, label="R_t")
    ax1.set_xlabel("R [kpc]")
    ax1.set_ylabel("W, Σ_gas(norm)")
    ax1.set_ylim(0, 1.1)
    ax1.legend(fontsize=8)

    plt.tight_layout()
    out_png = os.path.join("image", f"{galaxy_tag}_v2_summary.png")
    plt.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"Saved {out_png}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: fdb2_fit.py <sparc_csv>")
        sys.exit(1)
    fit_galaxy_v2(sys.argv[1])
