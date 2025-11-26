#!/usr/bin/env python3
"""
Closed-form estimator for the FDB correlation length (lambda_C) and photon mass (m_gamma).

For each SPARC galaxy we assume the minimal switch model
    v_obs^2(r) = v_bar^2(r) + v_flat^2 * (1 - exp(-r/lambda))
with v_flat fixed by the BTFR amplitude.
Solving point-by-point gives
    lambda(r) = - r / ln(1 - Delta(r)),
where Delta = (v_obs^2 - v_bar^2) / v_flat^2.
We keep only points with 0.15 < Delta < 0.85 and reasonable velocity errors.
Each galaxy contributes the weighted median of its valid lambda(r),
and the global lambda is the median of galaxy medians.

Outputs (JSON):
    - lambdaC_kpc_median, mad, lo/hi (approx 1-sigma)
    - m_gamma (kg and eV equivalents) with propagated bounds
    - per-galaxy statistics for diagnostics

This script is intentionally lightweight (no non-linear optimisation).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from helpers_sparc import glob_rotmods, load_sparc_catalog, parse_rotmod_file

# Physical constants (SI)
HBAR = 1.054_571_817e-34  # J s
C = 2.997_924_58e8        # m/s
KPC = 3.085_677_581e19    # m
KG_TO_EV = 1.0 / 1.782_661_92e-36  # eV per kg


def m_from_lambda_kpc(lam_kpc: float) -> float:
    lam_m = lam_kpc * KPC
    return HBAR / (C * lam_m)


def eV_from_kg(m_kg: float) -> float:
    return m_kg * KG_TO_EV


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    if values.size == 0:
        raise ValueError("no data for weighted median")
    sorter = np.argsort(values)
    v = values[sorter]
    w = weights[sorter]
    cum = np.cumsum(w)
    cutoff = 0.5 * cum[-1]
    idx = np.searchsorted(cum, cutoff)
    return float(v[min(idx, len(v) - 1)])


def robust_interval(samples: np.ndarray) -> Tuple[float, float, float]:
    """Return (median, lo, hi) using MAD*1.4826 as 1 sigma equivalent."""
    med = float(np.median(samples))
    mad = 1.4826 * np.median(np.abs(samples - med))
    lo = med - mad
    hi = med + mad
    return med, max(lo, 1e-6), max(hi, 1e-6)


def prepare_catalog(rotmod_dir: str, catalog_path: str, A_btfr: float,
                    min_points: int) -> List[Tuple[str, float, pd.DataFrame]]:
    cat = load_sparc_catalog(catalog_path)
    name2M = {str(r["name"]).strip().lower(): float(r["Mbar"]) for _, r in cat.iterrows()}
    galaxies = []
    for p in glob_rotmods(rotmod_dir):
        name = p.name.replace("_rotmod.dat", "").lower()
        Mbar = name2M.get(name)
        if Mbar is None or Mbar <= 0:
            continue
        vflat = float((A_btfr * Mbar) ** 0.25)
        df = parse_rotmod_file(p)
        if df.empty or len(df) < min_points:
            continue
        galaxies.append((name, vflat, df))
    if not galaxies:
        raise RuntimeError("no usable SPARC galaxies found")
    return galaxies


def per_point_lambda(df: pd.DataFrame, vflat: float,
                     delta_min: float, delta_max: float,
                     error_floor: float) -> Tuple[np.ndarray, np.ndarray]:
    r = df["r_kpc"].values
    vobs = df["v_obs"].values
    eobs = df["e_obs"].fillna(error_floor).values
    eobs = np.maximum(eobs, error_floor)
    vbar_sq = (df["v_gas"] ** 2 + df["v_disk"] ** 2 + df["v_bulge"] ** 2).values
    delta = (vobs ** 2 - vbar_sq) / max(vflat ** 2, 1e-12)

    mask = (
        (delta > delta_min) &
        (delta < delta_max) &
        (vobs > 0) &
        (~np.isnan(delta)) &
        (np.abs(vobs - np.sqrt(vbar_sq)) > 0.1)  # avoid exact cancellation
    )
    if not np.any(mask):
        return np.array([]), np.array([])
    delta = delta[mask]
    r = r[mask]
    eobs = eobs[mask]

    denom = np.log(1.0 - delta)
    denom = np.where(denom == 0, np.nan, denom)
    lam = -r / denom
    lam = lam[np.isfinite(lam) & (lam > 0)]
    w = 1.0 / (eobs[:len(lam)] ** 2) if len(lam) else np.array([])
    return lam, w


def main():
    ap = argparse.ArgumentParser(description="Closed-form lambda_C estimator from SPARC data.")
    ap.add_argument("--rotmod_dir", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--btfr_json", required=True)
    ap.add_argument("--delta_min", type=float, default=0.15)
    ap.add_argument("--delta_max", type=float, default=0.85)
    ap.add_argument("--error_floor", type=float, default=5.0)
    ap.add_argument("--min_points", type=int, default=5)
    ap.add_argument("--out_json", required=True)
    args = ap.parse_args()

    with open(args.btfr_json) as f:
        A_btfr = float(json.load(f)["A_BTFR_median"])

    galaxies = prepare_catalog(args.rotmod_dir, args.catalog, A_btfr, args.min_points)
    gal_results: Dict[str, Dict[str, float]] = {}
    lam_gal = []

    for name, vflat, df in galaxies:
        lam_pts, weights = per_point_lambda(
            df, vflat, args.delta_min, args.delta_max, args.error_floor
        )
        if lam_pts.size == 0:
            continue
        try:
            lam_med = weighted_median(lam_pts, weights if weights.size else np.ones_like(lam_pts))
        except ValueError:
            continue
        lam_gal.append(lam_med)
        gal_results[name] = {
            "lambdaC_kpc_median": float(lam_med),
            "n_points": int(lam_pts.size)
        }

    lam_gal = np.array(lam_gal)
    lam_med, lam_lo, lam_hi = robust_interval(lam_gal)
    m_med = m_from_lambda_kpc(lam_med)
    m_lo = m_from_lambda_kpc(lam_hi)  # hi lambda => low mass
    m_hi = m_from_lambda_kpc(lam_lo)

    result = {
        "lambdaC_kpc_galaxies": gal_results,
        "lambdaC_kpc_median": lam_med,
        "lambdaC_kpc_lo": lam_lo,
        "lambdaC_kpc_hi": lam_hi,
        "lambdaC_kpc_mad": 0.5 * (lam_hi - lam_lo),
        "m_gamma_kg_median": m_med,
        "m_gamma_kg_lo": m_lo,
        "m_gamma_kg_hi": m_hi,
        "m_gamma_eV_median": eV_from_kg(m_med),
        "m_gamma_eV_lo": eV_from_kg(m_lo),
        "m_gamma_eV_hi": eV_from_kg(m_hi),
        "N_galaxies": int(len(gal_results)),
        "delta_window": [args.delta_min, args.delta_max],
        "error_floor_kms": args.error_floor,
    }

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
