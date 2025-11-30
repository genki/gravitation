#!/usr/bin/env python3
"""
Multi-galaxy FDB fit with common (alpha, mu) and per-galaxy (ML_scale, R_ev/Rd, sigma_ev/Rd).

This uses the same Newton+1/r competitive mixing model as fdb_fit.py, but fits a
single (alpha, mu) across multiple galaxies while allowing each galaxy to have
its own ML_scale and shell geometry (R_ev/Rd, sigma_ev/Rd), with a prior that
keeps R_ev close to the radius where Sigma_gas drops most steeply.
"""

import sys
import os
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize
import matplotlib.pyplot as plt


@dataclass
class Galaxy:
    name: str
    R: np.ndarray
    Vobs: np.ndarray
    eVobs: np.ndarray
    Vdisk: np.ndarray
    Vgas: np.ndarray
    Vbul: np.ndarray
    Vnewt: np.ndarray
    Sigma_gas: np.ndarray
    Sigma_star: np.ndarray
    Rd: float
    R_ev_est: float
    sigma_R_ev: float
    r_cut: float
    S_scale: float  # gas-based scaling for FDB strength (set later)


def load_galaxy(csv_path: str, name: str) -> Galaxy:
    df = pd.read_csv(csv_path)
    R = df["R_kpc"].to_numpy()
    Vobs = df["Vobs"].to_numpy()
    eVobs = df["eVobs"].to_numpy()
    Vdisk = df.get("Vdisk_rotmod", pd.Series(np.zeros(len(df)))).to_numpy()
    Vgas = df.get("Vgas_rotmod", pd.Series(np.zeros(len(df)))).to_numpy()
    Vbul = df.get("Vbul_rotmod", pd.Series(np.zeros(len(df)))).to_numpy()
    Vnewt = np.sqrt(np.clip(Vdisk**2 + Vgas**2 + Vbul**2, 0, None))
    Sigma_gas = df["Sigma_gas"].to_numpy()
    Sigma_star = df["Sigma_star"].to_numpy()

    # Estimate Rd from Sigma_star (simple exponential fit as in fdb_fit.py)
    mask_star = Sigma_star > np.max(Sigma_star) * 1e-3
    if mask_star.sum() >= 5:
        Rm = R[mask_star]
        Sm = Sigma_star[mask_star]
        coeffs = np.polyfit(Rm, np.log(np.clip(Sm, 1e-12, None)), 1)
        slope = coeffs[0]
        if slope < 0:
            Rd = -1.0 / slope
        else:
            Rd = np.median(R)
    else:
        Rd = np.median(R)

    # Estimate shell center and its uncertainty from Sigma_gas
    R_ev_est, sigma_R_ev = estimate_shell_from_sigma(R, Sigma_gas)

    # Fit domain: R > Rd (same criterion as single-galaxy fitter)
    r_cut = Rd

    return Galaxy(
        name=name,
        R=R,
        Vobs=Vobs,
        eVobs=eVobs,
        Vdisk=Vdisk,
        Vgas=Vgas,
        Vbul=Vbul,
        Vnewt=Vnewt,
        Sigma_gas=Sigma_gas,
        Sigma_star=Sigma_star,
        Rd=Rd,
        R_ev_est=R_ev_est,
        sigma_R_ev=sigma_R_ev,
        r_cut=r_cut,
        S_scale=1.0,
    )


def estimate_shell_from_sigma(R: np.ndarray, Sigma_gas: np.ndarray) -> Tuple[float, float]:
    R = np.asarray(R)
    Sig = np.asarray(Sigma_gas)
    mask = np.isfinite(R) & np.isfinite(Sig) & (Sig > 0)
    if mask.sum() < 4:
        R_med = np.median(R[mask]) if mask.any() else np.median(R)
        return float(R_med), float(0.5 * R_med)
    Rm = R[mask]
    Sm = Sig[mask]
    Sm_smooth = pd.Series(Sm).rolling(window=3, center=True, min_periods=1).mean().to_numpy()
    dS = np.gradient(Sm_smooth, Rm)
    idx = int(np.argmin(dS))
    R_ev_est = float(Rm[idx])
    thresh = 0.5 * dS[idx]
    left = idx
    while left > 0 and dS[left] <= thresh:
        left -= 1
    right = idx
    while right < len(Rm) - 1 and dS[right] <= thresh:
        right += 1
    sigma_R = 0.5 * (Rm[right] - Rm[left]) if right > left else 0.3 * R_ev_est
    return R_ev_est, float(abs(sigma_R))


def chi2_multi(vec: np.ndarray, gals: List[Galaxy], sigma_model: float = 8.0) -> float:
    """
    vec structure:
      [alpha, mu,
       ML_0..ML_{N-1},
       RevScale_0..RevScale_{N-1},
       SigScale_0..SigScale_{N-1}]
    """
    n = len(gals)
    alpha = vec[0]
    mu = np.clip(vec[1], 0.3, 1.0)
    ML = vec[2 : 2 + n]
    RevScale = vec[2 + n : 2 + 2 * n]
    SigScale = vec[2 + 2 * n : 2 + 3 * n]

    if alpha < 0:
        alpha = 0.0

    chi2_tot = 0.0
    for i, g in enumerate(gals):
        ml_i = ML[i]
        if not (0.6 <= ml_i <= 1.0):
            return 1e30
        # Gas-dependent geometric scaling for the shell radius:
        # gas-rich systems have the evanescent layer slightly farther out,
        # gas-poor dwarfs slightly closer in.
        scale = g.S_scale
        geom_factor = 1.0 + 0.5 * (scale - 1.0) / (1.0 + abs(scale - 1.0))
        R_ev = RevScale[i] * g.Rd * geom_factor
        sigma_ev = SigScale[i] * g.Rd
        if sigma_ev <= 0:
            return 1e30

        # Fit domain
        mask = g.R > g.r_cut
        if not np.any(mask):
            return 1e30
        R = g.R[mask]
        Vobs = g.Vobs[mask]
        eV = g.eVobs[mask]
        Vn = g.Vnewt[mask]

        # Transition weight: 0 -> 1 (inner -> outer)
        w = 1.0 / (1.0 + np.exp(-(R - R_ev) / sigma_ev))
        w = np.clip(w, 0.0, 1.0)

        A_F = mu * w
        A_N = 1.0 - A_F

        # Common FDB strength alpha; geometry (R_ev) already accounts for gas content
        v2_tot = (A_N * ml_i * Vn) ** 2 + A_F * alpha
        V_tot = np.sqrt(np.clip(v2_tot, 0.0, None))

        err = np.sqrt(eV**2 + sigma_model**2)
        chi = (Vobs - V_tot) / err
        chi2 = float(np.sum(chi**2))

        # Prior on R_ev from Sigma_gas-based estimate
        if g.sigma_R_ev > 0:
            chi2 += ((R_ev - g.R_ev_est) / g.sigma_R_ev) ** 2

        chi2_tot += chi2

    return chi2_tot


def make_summary_plot(
    g: Galaxy,
    alpha: float,
    mu: float,
    ml_scale: float,
    RevScale: float,
    SigScale: float,
    sigma_model: float = 8.0,
) -> None:
    """Make a per-galaxy summary plot using common (alpha, mu) and given per-galaxy params."""
    os.makedirs("out", exist_ok=True)

    R = g.R
    Vn = g.Vnewt
    scale = g.S_scale
    geom_factor = 1.0 + 0.5 * (scale - 1.0) / (1.0 + abs(scale - 1.0))
    R_ev = RevScale * g.Rd * geom_factor
    sigma_ev = SigScale * g.Rd

    if sigma_ev > 0:
        w_all = 1.0 / (1.0 + np.exp(-(R - R_ev) / sigma_ev))
    else:
        w_all = np.zeros_like(R)
    w_all = np.clip(w_all, 0.0, 1.0)
    mu = np.clip(mu, 0.3, 1.0)
    A_F = mu * w_all
    A_N = 1.0 - A_F

    alpha = max(alpha, 0.0)
    v2_tot_all = (A_N * ml_scale * Vn) ** 2 + A_F * alpha
    V_tot = np.sqrt(np.clip(v2_tot_all, 0.0, None))

    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(7, 6))

    # Top: rotation curves
    ax0.errorbar(R, g.Vobs, yerr=g.eVobs, fmt="o", ms=3, label="Vobs")
    ax0.plot(R, Vn, label="Newton (rotmod)")
    ax0.plot(R, V_tot, label="FDB total (common)")
    ax0.set_ylabel("V [km/s]")
    ax0.legend()

    # Bottom: normalized profiles
    def norm_series(arr: np.ndarray) -> np.ndarray:
        m = np.nanmax(np.abs(arr))
        if m <= 0:
            return np.zeros_like(arr)
        return arr / m

    series = {
        "errV": norm_series(g.eVobs),
        "Vgas": norm_series(g.Vgas),
        "Vdisk": norm_series(g.Vdisk),
        "Vbul": norm_series(g.Vbul),
        r"$\Sigma_{\rm gas}$": norm_series(g.Sigma_gas),
    }
    # Star: normalize using R > r_cut to emphasize outer disk
    mask_outer = R > g.r_cut
    star_vals = g.Sigma_star
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
    out_path = os.path.join("out", f"{g.name}_multi_summary.png")
    plt.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    # Galaxies to include
    gals = [
        load_galaxy("build/NGC2403_sparc.csv", "NGC2403"),
        load_galaxy("build/NGC3198_sparc.csv", "NGC3198"),
        load_galaxy("build/NGC6503_sparc.csv", "NGC6503"),
        load_galaxy("build/DDO170_sparc.csv", "DDO170"),
        load_galaxy("build/DDO168_sparc.csv", "DDO168"),
    ]
    n = len(gals)

    # Set S_scale for each galaxy based on its gas content:
    # use total gas mass proxy from Sigma_gas profile.
    gas_masses = []
    for g in gals:
        R = g.R
        Sig = g.Sigma_gas  # Msun/pc^2
        # rough integration: convert to Msun/kpc^2 and integrate 2πR dR
        Sig_kpc2 = Sig * 1e6
        dR = np.gradient(R)
        M_approx = float(np.sum(2.0 * np.pi * R * Sig_kpc2 * dR))
        gas_masses.append(max(M_approx, 0.0))
    gas_masses = np.array(gas_masses)
    med_mass = np.median(gas_masses[gas_masses > 0]) if np.any(gas_masses > 0) else 1.0
    for g, M in zip(gals, gas_masses):
        g.S_scale = float(M / med_mass) if med_mass > 0 else 1.0

    # Initial guess: alpha ~ 5e3–5e4, mu~0.7, ML~0.9, RevScale~2.5, SigScale~0.7
    alpha0 = 5e3
    mu0 = 0.7
    ML0 = np.full(n, 0.9)
    Rev0 = np.full(n, 2.5)
    Sig0 = np.full(n, 0.7)
    x0 = np.concatenate([[alpha0, mu0], ML0, Rev0, Sig0])

    bounds = []
    bounds.append((0.0, 5e4))   # alpha
    bounds.append((0.3, 1.0))   # mu
    bounds.extend([(0.6, 1.0)] * n)   # ML_i
    bounds.extend([(2.0, 3.0)] * n)   # RevScale_i
    bounds.extend([(0.5, 1.0)] * n)   # SigScale_i

    res = minimize(
        lambda x: chi2_multi(x, gals),
        x0,
        method="L-BFGS-B",
        bounds=bounds,
    )

    print("Multi-galaxy fit result:")
    alpha_opt = res.x[0]
    mu_opt = res.x[1]
    print("  alpha (Δv^2_FDB) =", alpha_opt)
    print("  mu               =", mu_opt)
    ML = res.x[2 : 2 + n]
    RevScale = res.x[2 + n : 2 + 2 * n]
    SigScale = res.x[2 + 2 * n : 2 + 3 * n]
    for i, g in enumerate(gals):
        print(f"  [{g.name}] ML={ML[i]:.3f}, R_ev/Rd={RevScale[i]:.3f}, sigma_ev/Rd={SigScale[i]:.3f}")
    print("  chi2_total       =", res.fun)

    # Produce summary plots under the common parameters
    for i, g in enumerate(gals):
        make_summary_plot(
            g,
            alpha=alpha_opt,
            mu=mu_opt,
            ml_scale=ML[i],
            RevScale=RevScale[i],
            SigScale=SigScale[i],
        )


if __name__ == "__main__":
    main()
