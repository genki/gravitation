import argparse
import json
from pathlib import Path

import numpy as np

from helpers_sparc import glob_rotmods, load_sparc_catalog, parse_rotmod_file

# Physical constants (SI units)
HBAR = 1.054_571_817e-34  # J s
C = 2.997_924_58e8        # m/s
KPC = 3.085_677_581e19    # m
KG_TO_EV = 1.0 / 1.782_661_92e-36  # eV per kg


def m_from_lambda_kpc(lambda_kpc: float) -> float:
    """Convert correlation length (kpc) to photon mass (kg)."""
    lam_m = lambda_kpc * KPC
    return HBAR / (C * lam_m)


def eV_from_kg(m_kg: float) -> float:
    return m_kg * KG_TO_EV


# sanity check (few per-mille tolerance)
assert abs(m_from_lambda_kpc(51) / 2.24e-64 - 1) < 5e-3
assert abs(eV_from_kg(2.24e-64) / 1.26e-28 - 1) < 5e-3


def load_btfr(btfr_json: str) -> float:
    with open(btfr_json) as f:
        data = json.load(f)
    return float(data["A_BTFR_median"])


def S_switch(r_kpc, lambda_kpc):
    lam = max(lambda_kpc, 1e-3)
    return 1.0 - np.exp(-np.asarray(r_kpc) / lam)


def v_model_sq(vbar_sq, vflat, r_kpc, lambda_kpc):
    return vbar_sq + (vflat ** 2) * S_switch(r_kpc, lambda_kpc)


def galaxy_residual(df, vflat, lambda_kpc, error_floor):
    vbar_sq = (df["v_gas"] ** 2 + df["v_disk"] ** 2 + df["v_bulge"] ** 2).values
    vmod = np.sqrt(v_model_sq(vbar_sq, vflat, df["r_kpc"].values, lambda_kpc))
    e = df["e_obs"].fillna(error_floor).values
    e = np.maximum(e, error_floor)
    w = 1.0 / (e ** 2)
    resid = df["v_obs"].values - vmod
    return resid, w


def robust_cost(resid, w):
    if resid.size == 0:
        return np.inf
    scaled = resid * np.sqrt(w / np.median(w))
    med = np.median(scaled)
    return float(1.4826 * np.median(np.abs(scaled - med)))


def prepare_galaxies(rotmod_dir, catalog_path, A_btfr):
    cat = load_sparc_catalog(catalog_path)
    name2M = {str(row["name"]).lower(): float(row["Mbar"]) for _, row in cat.iterrows()}
    galaxies = []
    for p in glob_rotmods(rotmod_dir):
        name = p.name.replace("_rotmod.dat", "").lower()
        if name not in name2M:
            continue
        Mbar = name2M[name]
        if Mbar <= 0:
            continue
        vflat = float((A_btfr * Mbar) ** 0.25)
        df = parse_rotmod_file(p)
        if df.empty or len(df) < 5:
            continue
        galaxies.append((name, vflat, df))
    if not galaxies:
        raise RuntimeError("no SPARC galaxies available")
    return galaxies


def sweep_lambda(galaxies, grid, error_floor):
    costs = []
    for lam in grid:
        c = []
        for _, vflat, df in galaxies:
            resid, w = galaxy_residual(df, vflat, lam, error_floor)
            c.append(robust_cost(resid, w))
        costs.append(float(np.median(c)))
    costs = np.array(costs)
    idx = int(np.argmin(costs))
    return costs, idx


def curvature_interval(grid, costs, idx):
    j0 = max(idx - 2, 0)
    j1 = min(idx + 3, len(grid))
    x = np.log10(grid[j0:j1])
    y = costs[j0:j1]
    if len(x) < 3:
        lam = grid[idx]
        return lam / 2, lam, lam * 2
    A = np.vstack([x ** 2, x, np.ones_like(x)]).T
    a, b, c = np.linalg.lstsq(A, y, rcond=None)[0]
    if a <= 0:
        lam = grid[idx]
        return lam / 2, lam, lam * 2
    x0 = -b / (2 * a)
    lam_hat = 10 ** x0
    y_hat = a * x0 * x0 + b * x0 + c
    scatter = np.std(y - (a * x ** 2 + b * x + c))
    if scatter <= 0:
        return lam_hat / 2, lam_hat, lam_hat * 2
    dx = np.sqrt(scatter / a)
    return 10 ** (x0 - dx), lam_hat, 10 ** (x0 + dx)


def bootstrap_lambda(galaxies, grid, error_floor, n_boot=200, seed=1234):
    rng = np.random.default_rng(seed)
    samples = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(galaxies), len(galaxies))
        sel = [galaxies[i] for i in idx]
        costs, imin = sweep_lambda(sel, grid, error_floor)
        samples.append(float(grid[imin]))
    samples = np.array(samples)
    return {
        "lambdaC_kpc_bootstrap_lo": float(np.percentile(samples, 16)),
        "lambdaC_kpc_bootstrap_hi": float(np.percentile(samples, 84)),
        "lambdaC_samples": samples.tolist(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rotmod_dir", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--btfr_json", required=True)
    ap.add_argument("--grid_min_kpc", type=float, default=30.0)
    ap.add_argument("--grid_max_kpc", type=float, default=3000.0)
    ap.add_argument("--n_grid", type=int, default=80)
    ap.add_argument("--error_floor", type=float, default=5.0)
    ap.add_argument("--n_boot", type=int, default=200)
    ap.add_argument("--crossfold", action="store_true", help="run simple 2-fold diagnostic")
    ap.add_argument("--out_json", required=True)
    ap.add_argument("--out_plot", default=None)
    args = ap.parse_args()

    A_btfr = load_btfr(args.btfr_json)
    galaxies = prepare_galaxies(args.rotmod_dir, args.catalog, A_btfr)
    grid = np.geomspace(args.grid_min_kpc, args.grid_max_kpc, args.n_grid)
    costs, idx = sweep_lambda(galaxies, grid, args.error_floor)
    lam_lo, lam_hat, lam_hi = curvature_interval(grid, costs, idx)

    m_hat = m_from_lambda_kpc(lam_hat)
    m_lo = m_from_lambda_kpc(lam_hi)
    m_hi = m_from_lambda_kpc(lam_lo)

    result = {
        "lambdaC_kpc_grid": grid.tolist(),
        "misfit": costs.tolist(),
        "lambdaC_kpc_hat": lam_hat,
        "lambdaC_kpc_lo": lam_lo,
        "lambdaC_kpc_hi": lam_hi,
        "m_gamma_kg_hat": m_hat,
        "m_gamma_kg_lo": m_lo,
        "m_gamma_kg_hi": m_hi,
        "m_gamma_eV_hat": eV_from_kg(m_hat),
        "m_gamma_eV_lo": eV_from_kg(m_lo),
        "m_gamma_eV_hi": eV_from_kg(m_hi),
        "N_galaxies": len(galaxies),
    }

    if args.n_boot > 0:
        boot = bootstrap_lambda(galaxies, grid, args.error_floor, args.n_boot)
        result.update(boot)
        lam_med = np.median(boot["lambdaC_samples"])
        result["m_gamma_kg_bootstrap_med"] = m_from_lambda_kpc(lam_med)
        result["m_gamma_eV_bootstrap_med"] = eV_from_kg(result["m_gamma_kg_bootstrap_med"])

    if args.crossfold:
        fold_vals = []
        fold_grid = np.geomspace(args.grid_min_kpc, args.grid_max_kpc, args.n_grid)
        even = [galaxies[i] for i in range(len(galaxies)) if i % 2 == 0]
        odd = [galaxies[i] for i in range(len(galaxies)) if i % 2 == 1]
        for subset in (even, odd):
            if not subset:
                continue
            _, idx_fold = sweep_lambda(subset, fold_grid, args.error_floor)
            fold_vals.append(float(fold_grid[idx_fold]))
        if fold_vals:
            result["lambdaC_kpc_crossfold"] = fold_vals
            result["m_gamma_kg_crossfold"] = [m_from_lambda_kpc(l) for l in fold_vals]
            result["m_gamma_eV_crossfold"] = [eV_from_kg(m) for m in result["m_gamma_kg_crossfold"]]

    Path(args.out_json).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump(result, f, indent=2)

    if args.out_plot:
        try:
            import matplotlib.pyplot as plt

            plt.figure()
            plt.plot(grid, costs)
            plt.xscale("log")
            plt.xlabel(r"$\lambda_C$ [kpc]")
            plt.ylabel("robust misfit (MAD)")
            plt.axvline(lam_hat, ls="--")
            plt.tight_layout()
            plt.savefig(args.out_plot, dpi=160)
        except Exception as exc:
            print("[warn] plot failed:", exc)


if __name__ == "__main__":
    main()
