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

# Provisional global thickness of the evanescent shell [kpc].
# In FDB picture this should be set by ULE-EM frequency / Compton scale and
# is expected to be roughly common across similar galaxies.
D_R_CONST_KPC = 1.0


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
    Diagnostic helper: estimate (R_t_est, dR_est) from Sigma_gas.
    v2 kernel now defines R_t mainly from stellar/bulge scales, so this is used
    only for logging.
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


def estimate_Rd_and_bulge_edge(R: np.ndarray, Sigma_star: np.ndarray, Vbul: np.ndarray, Vdisk: np.ndarray) -> Tuple[float, float]:
    """
    Estimate disk scale length Rd from Sigma_star and a bulge edge radius
    from the Vbul/Vtot ratio. If bulge is negligible, R_bulge_edge ~ 0.
    """
    R = np.asarray(R)
    Sig = np.asarray(Sigma_star)
    # Rd from exponential fit
    mask_star = Sig > np.max(Sig) * 1e-3
    if mask_star.sum() >= 5:
        Rm = R[mask_star]
        Sm = Sig[mask_star]
        coeffs = np.polyfit(Rm, np.log(np.clip(Sm, 1e-12, None)), 1)
        slope = coeffs[0]
        if slope < 0:
            Rd = -1.0 / slope
        else:
            Rd = np.median(R)
    else:
        Rd = np.median(R)

    # Bulge edge from Vbul fraction
    Vb = np.asarray(Vbul)
    Vd = np.asarray(Vdisk)
    Vtot = np.sqrt(np.clip(Vb**2 + Vd**2, 1e-6, None))
    frac = np.where(Vtot > 0, Vb / Vtot, 0.0)
    # bulge-dominated where frac > 0.3
    mask_b = frac > 0.3
    if np.any(mask_b):
        R_bulge_edge = float(R[np.where(mask_b)[0][-1]])
    else:
        R_bulge_edge = 0.0
    return float(Rd), float(R_bulge_edge)


def transition_weight(R: np.ndarray, R_t: float, dR: float) -> np.ndarray:
    if dR <= 0:
        return np.zeros_like(R)
    x = (R - R_t) / dR
    return 0.5 * (1.0 + np.tanh(x))


def chi2_v2(
    vec: np.ndarray,
    g: GalaxyData,
    sigma_model: float = 8.0,
) -> float:
    """
    Parameter vector: [Delta_v2, eps, kappa]
    with a global shell thickness dR = D_R_CONST_KPC.
    R_t is defined as bulge_edge + kappa * Rd.
    """
    Delta_v2, eps, kappa = vec
    dR = D_R_CONST_KPC
    if Delta_v2 < 0 or not (0.0 <= eps <= 0.5):
        return 1e30

    R = g.R_kpc
    Vobs = g.Vobs
    eV = g.eVobs
    Vn = np.sqrt(np.clip(g.Vdisk**2 + g.Vgas**2 + g.Vbul**2, 0, None))

    # Disk scale and bulge edge from stellar profile and Vbul/Vdisk
    Rd, R_bulge_edge = estimate_Rd_and_bulge_edge(R, g.Sigma_star, g.Vbul, g.Vdisk)
    R_t = R_bulge_edge + kappa * Rd
    if R_t <= 0:
        return 1e30

    W = transition_weight(R, R_t, dR)
    # v_tot^2 = v_Newt^2 * (1 - eps W) + Delta_v2 W
    v2_tot = (1.0 - eps * W) * (Vn**2) + Delta_v2 * W
    V_tot = np.sqrt(np.clip(v2_tot, 0.0, None))

    err = np.sqrt(eV**2 + sigma_model**2)
    # Fit only beyond stellar disk. Dwarfs (low Vmax) use a slightly looser cut.
    vmax = float(np.nanmax(Vobs))
    if vmax < 80.0:
        # dwarf / low-mass: relax to R > 2 Rd
        R_star_edge = 2.0 * Rd
    else:
        # L* spirals: keep R > 3 Rd
        R_star_edge = 3.0 * Rd
    mask_fit = R > R_star_edge
    if not np.any(mask_fit):
        return 1e30

    chi = (Vobs[mask_fit] - V_tot[mask_fit]) / err[mask_fit]
    chi2 = float(np.sum(chi**2))
    return chi2


def fit_galaxy_v2(csv_path: str):
    g = load_sparc_csv(csv_path)
    galaxy_tag = os.path.splitext(os.path.basename(csv_path))[0].replace("_sparc", "")

    # Diagnostic Sigma_gas-based transition (for logging only)
    R_t_est, dR_est = estimate_transition_radius(g.R_kpc, g.Sigma_gas)
    print(f"Sigma_gas-based transition (diagnostic): R_t ≈ {R_t_est:.2f} kpc, dR ≈ {dR_est:.2f} kpc")

    # Rd and bulge edge from stars (used for R_t definition)
    Rd, R_bulge_edge = estimate_Rd_and_bulge_edge(g.R_kpc, g.Sigma_star, g.Vbul, g.Vdisk)
    print(f"Estimated Rd ≈ {Rd:.2f} kpc, bulge edge ≈ {R_bulge_edge:.2f} kpc")

    # Initial guess: Delta_v2 from outer observed v^2, eps small, kappa~3
    mask_outer = g.R_kpc > 3.0 * Rd
    if np.any(mask_outer):
        v_outer = np.median(g.Vobs[mask_outer])
        v_newt_outer = np.median(np.sqrt(np.clip(
            g.Vdisk[mask_outer]**2 + g.Vgas[mask_outer]**2 + g.Vbul[mask_outer]**2, 0, None)))
        Delta0 = max(v_outer**2 - v_newt_outer**2, 0.0)
    else:
        Delta0 = 0.0
    # Dwarf vs L* handling for kappa bounds
    vmax = float(np.nanmax(g.Vobs))
    if vmax < 80.0:
        # dwarf / low-mass: allow R_t to start as close as 0.5 Rd
        kappa_min = 0.5
        kappa_init = 1.5
    else:
        # L* spirals: keep kappa >= 1
        kappa_min = 1.0
        kappa_init = 3.0
    x0 = np.array([Delta0, 0.2, kappa_init])
    bounds = [
        (0.0, 5e4),      # Delta_v2
        (0.0, 0.5),      # eps
        (kappa_min, 5.0),      # kappa (offset in Rd units)
    ]

    res = minimize(
        lambda x: chi2_v2(x, g),
        x0,
        method="L-BFGS-B",
        bounds=bounds,
    )
    print("Best-fit v2 params [Delta_v2, eps, kappa]:", res.x)
    print("chi2_v2 =", res.fun)

    # Build model curve
    Delta_v2, eps, kappa = res.x
    R = g.R_kpc
    Vn = np.sqrt(np.clip(g.Vdisk**2 + g.Vgas**2 + g.Vbul**2, 0, None))
    Rd, R_bulge_edge = estimate_Rd_and_bulge_edge(R, g.Sigma_star, g.Vbul, g.Vdisk)
    R_t = R_bulge_edge + kappa * Rd
    W = transition_weight(R, R_t, D_R_CONST_KPC)
    v2_tot = (1.0 - eps * W) * (Vn**2) + Delta_v2 * W
    V_tot = np.sqrt(np.clip(v2_tot, 0.0, None))

    # Report chi2 for outer (fit), inner, and all radii for evaluation
    err_all = np.sqrt(g.eVobs**2 + 8.0**2)
    R_star_edge = 3.0 * Rd
    mask_outer = R > R_star_edge
    mask_inner = ~mask_outer
    def safe_chi2(mask):
        if not np.any(mask):
            return float("nan")
        chi = (g.Vobs[mask] - V_tot[mask]) / err_all[mask]
        return float(np.sum(chi**2))
    chi2_outer = safe_chi2(mask_outer)
    chi2_inner = safe_chi2(mask_inner)
    chi2_all = safe_chi2(np.isfinite(R))
    print(f"chi2_v2 (outer, R>3Rd) = {chi2_outer:.3f}")
    print(f"chi2_v2 (inner, R<=3Rd) = {chi2_inner:.3f}")
    print(f"chi2_v2 (all radii) = {chi2_all:.3f}")

    # Plot
    os.makedirs("out", exist_ok=True)
    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(7, 6))

    ax0.errorbar(R, g.Vobs, yerr=g.eVobs, fmt="o", ms=3, label="Vobs")
    ax0.plot(R, Vn, label="Newton (rotmod)")
    ax0.plot(R, V_tot, label="FDB v2 total")
    ax0.set_ylabel("V [km/s]")
    ax0.legend()
    ax0.set_title(galaxy_tag)

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
    out_png = os.path.join("out", f"{galaxy_tag}_v2_summary.png")
    plt.savefig(out_png, dpi=150)
    plt.close(fig)
    print(f"Saved {out_png}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: fdb2_fit.py <sparc_csv>")
        sys.exit(1)
    fit_galaxy_v2(sys.argv[1])
