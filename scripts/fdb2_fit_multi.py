#!/usr/bin/env python3
"""
FDB rotation-curve fit (v2 kernel), multi-galaxy version.

We use the per-galaxy v2 kernel from `fdb2_fit.py`:

    v_tot^2(R) = v_Newt^2(R) * (1 - eps * W(R)) + Delta_v2 * W(R)

with a global shell thickness dR = D_R_CONST_KPC, and

    R_t(g) = R_bulge_edge(g) + kappa_g * Rd(g)

for each galaxy g. Here we fit:

  - global parameters: Delta_v2, eps
  - per-galaxy parameters: kappa_g for each galaxy

against the outer-disk chi^2 (the same definition as chi2_v2 in fdb2_fit.py).

This script is intended as a lightweight "common kernel" test across
the current working set of 16 galaxies (L* spirals + dwarfs).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from fdb2_fit import (
    GalaxyData,
    load_sparc_csv,
    chi2_v2,
)


GALAXY_TAGS = [
    # L* spirals
    "NGC2403",
    "NGC3198",
    "NGC6503",
    "NGC2903",
    "NGC3521",
    "NGC5055",
    "NGC7331",
    "NGC5005",
    "NGC7793",
    # dwarfs / low-mass
    "NGC2366",
    "NGC3109",
    "DDO064",
    "DDO161",
    "DDO168",
    "DDO170",
    "KK98-251",
]


def load_galaxies() -> List[Tuple[str, GalaxyData]]:
    galaxies: List[Tuple[str, GalaxyData]] = []
    for tag in GALAXY_TAGS:
        csv_path = os.path.join("build", f"{tag}_sparc.csv")
        if not os.path.exists(csv_path):
            raise FileNotFoundError(csv_path)
        g = load_sparc_csv(csv_path)
        galaxies.append((tag, g))
    return galaxies


def total_chi2_multi(params: np.ndarray, galaxies: List[Tuple[str, GalaxyData]]) -> float:
    """
    params = [Delta_v2, eps, kappa_0, ..., kappa_{N-1}]
    chi2 = sum_g chi2_v2([Delta_v2, eps, kappa_g], g)
    """
    Delta_v2, eps = params[0], params[1]
    kappas = params[2:]
    if Delta_v2 < 0 or not (0.0 <= eps <= 0.5):
        return 1e30
    if len(kappas) != len(galaxies):
        return 1e30

    chi2_tot = 0.0
    for (tag, g), kappa in zip(galaxies, kappas):
        # kappa bounds enforced via optimizer; here just guard against nonsense
        if kappa <= 0.0 or kappa > 5.0:
            return 1e30
        vec = np.array([Delta_v2, eps, kappa])
        chi2_g = chi2_v2(vec, g)
        if not np.isfinite(chi2_g) or chi2_g >= 1e29:
            # penalize pathological fits
            return 1e30
        chi2_tot += chi2_g
    return float(chi2_tot)


def main():
    galaxies = load_galaxies()
    n_gal = len(galaxies)

    # Rough initial guess for Delta_v2: average of per-galaxy outer v^2 excess.
    # For simplicity we take a single representative value.
    # Here we approximate from a typical L* (can be refined if needed).
    Delta0 = 2.0e4
    eps0 = 0.2
    # Initial kappa: 3 for L* spirals, 1.5 for dwarfs (vmax<80 km/s)
    kappa0 = []
    for tag, g in galaxies:
        vmax = float(np.nanmax(g.Vobs))
        if vmax < 80.0:
            kappa0.append(1.5)
        else:
            kappa0.append(3.0)

    x0 = np.concatenate(([Delta0, eps0], np.array(kappa0)))

    # Bounds: Delta_v2>=0, 0<=eps<=0.5, kappa in [0.5,5] for dwarfs, [1,5] for L*
    bounds: List[Tuple[float, float]] = []
    bounds.append((0.0, 5e4))   # Delta_v2
    bounds.append((0.0, 0.5))   # eps
    for tag, g in galaxies:
        vmax = float(np.nanmax(g.Vobs))
        if vmax < 80.0:
            bounds.append((0.5, 5.0))
        else:
            bounds.append((1.0, 5.0))

    print(f"# galaxies in multi-fit: {n_gal}")
    res = minimize(
        lambda v: total_chi2_multi(v, galaxies),
        x0,
        method="L-BFGS-B",
        bounds=bounds,
    )

    Delta_v2, eps = res.x[0], res.x[1]
    kappas = res.x[2:]
    print("Best-fit global parameters:")
    print(f"  Delta_v2 = {Delta_v2:.3g}")
    print(f"  eps      = {eps:.3g}")
    print("Per-galaxy kappa (R_t = R_bulge_edge + kappa*Rd):")
    for (tag, g), kappa in zip(galaxies, kappas):
        print(f"  {tag:8s}: kappa = {kappa:.3g}")

    print("Total chi2 (outer-only sum) =", res.fun)


if __name__ == "__main__":
    main()

