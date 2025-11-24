"""
Lightweight SPARC fitting for FDB (k=1) vs NFW (k=2) with fixed M/L.
Assumptions (from instructions):
  - Y_disk = 0.5, Y_bulge = 0.7 (3.6µm)
  - velocity error floor = 5 km/s
  - quality / inclination filters are not applied because the metadata
    are not available in the bundled MRT; velocities are already
    inclination-corrected in SPARC rotmod files.
  - v_flat: median of points with r >= 3 R_d; if <2 points, median of
    outermost 3 points.
Outputs:
  - build/sparc_aicc.csv with per-galaxy chi2, AICc, ΔAICc (FDB−NFW),
    best-fit V0 (FDB) and best NFW params.
  - figures/btfr_sparc.png BTFR using v_flat & M_bar.
  - figures/rotcurve_NGC6503.png example rotation curve.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Globals that may be overridden via CLI
Y_DISK = 0.5
Y_BULGE = 0.7
ERR_FLOOR = 5.0  # km/s
GAS_FACTOR = 1.33

H0 = 70.0  # km/s/Mpc

DATA_DIR = Path("data/sparc/sparc_database")
MRT_FILE = Path("data/sparc/SPARC_Lelli2016c.mrt")
OUT_CSV = Path("paper2/build/sparc_aicc.csv")
FIG_BTFR = Path("paper2/figures/btfr_sparc.png")
FIG_ROT_GRID = Path("paper2/figures/rotcurve_grid.png")


def load_rotmod(path: Path):
    # Columns: R [kpc], Vobs, eVobs, Vgas, Vdisk, Vbul, ... (others unused)
    arr = np.loadtxt(path)
    r, vobs, eobs, vgas, vdisk, vbul = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3], arr[:, 4], arr[:, 5]
    return r, vobs, eobs, vgas, vdisk, vbul


def vbar_sq(vgas, vdisk, vbul):
    return vgas**2 + (Y_DISK * vdisk) ** 2 + (Y_BULGE * vbul) ** 2


def chi2(model, vobs, e):
    return np.sum((vobs - model) ** 2 / e**2)


def aicc(chi2_val, k, n):
    if n - k - 1 <= 0:
        return np.inf
    return chi2_val + 2 * k + 2 * k * (k + 1) / (n - k - 1)


def nfw_vcirc(r, c, v200):
    # r [kpc], v200 [km/s], H0 km/s/Mpc
    r200 = (v200 / (10 * H0)) * 1e3  # kpc
    x = r / r200
    g = np.log(1 + c) - c / (1 + c)
    vc2 = v200**2 * (np.log(1 + c * x) - (c * x) / (1 + c * x)) / (x * g + 1e-12)
    vc2 = np.clip(vc2, 0, None)
    return np.sqrt(vc2)


def fit_fdb(r, vobs, e, vbar2):
    vmin, vmax = 0.0, 450.0
    coarse = np.linspace(vmin, vmax, 91)
    best_chi = np.inf
    best_v0 = 0.0
    for v0 in coarse:
        model = np.sqrt(vbar2 + v0**2)
        c2 = chi2(model, vobs, e)
        if c2 < best_chi:
            best_chi, best_v0 = c2, v0
    fine = np.linspace(max(best_v0 - 10, vmin), min(best_v0 + 10, vmax), 81)
    for v0 in fine:
        model = np.sqrt(vbar2 + v0**2)
        c2 = chi2(model, vobs, e)
        if c2 < best_chi:
            best_chi, best_v0 = c2, v0
    return best_v0, best_chi


def fit_nfw(r, vobs, e, vbar2, c_fixed: float | None = None):
    c_grid = np.logspace(np.log10(2), np.log10(32), 21)
    v200_grid = np.linspace(50, 350, 21)
    best = (np.inf, None, None)
    c_space = [c_fixed] if c_fixed is not None else c_grid
    for c in c_space:
        for v200 in v200_grid:
            vhalo = nfw_vcirc(r, c, v200)
            model = np.sqrt(vbar2 + vhalo**2)
            c2 = chi2(model, vobs, e)
            if c2 < best[0]:
                best = (c2, c, v200)
    return best[1], best[2], best[0]


def vflat_median(r, vobs, rd):
    mask = r >= 3 * rd
    if mask.sum() >= 2:
        return np.median(vobs[mask])
    # fallback: outermost three points
    idx = np.argsort(r)[-3:]
    return np.median(vobs[idx])


def slope_delta_v2(r, vobs, vbar2, e):
    dv2 = vobs**2 - vbar2
    w = 1 / (e**2)
    W = np.sum(w)
    Wr = np.sum(w * r)
    Wr2 = np.sum(w * r**2)
    Wd = np.sum(w * dv2)
    Wrd = np.sum(w * r * dv2)
    denom = W * Wr2 - Wr ** 2 + 1e-12
    b = (W * Wrd - Wr * Wd) / denom
    return b


def load_btfr_catalog(mrt_path: Path, y_disk: float):
    cols = [
        "Galaxy",
        "T",
        "D",
        "e_D",
        "f_D",
        "Inc",
        "e_Inc",
        "L36",
        "e_L36",
        "Reff",
        "SBeff",
        "Rdisk",
        "SBdisk",
        "MHI",
        "RHI",
        "Vflat",
        "e_Vflat",
        "Q",
        "Refs",
    ]
    df = pd.read_fwf(mrt_path, skiprows=98, names=cols)
    df["Galaxy"] = df["Galaxy"].str.strip()
    mbar = (y_disk * df["L36"] + GAS_FACTOR * df["MHI"]) * 1e9
    vflat = df["Vflat"]
    mask = (
        np.isfinite(mbar)
        & np.isfinite(vflat)
        & (mbar > 0)
        & (vflat > 0)
    )
    return pd.DataFrame(
        {
            "galaxy": df.loc[mask, "Galaxy"].values,
            "mbar": mbar[mask].values,
            "vflat": vflat[mask].values,
        }
    )


def make_btfr_figure(cat_df: pd.DataFrame, fig_path: Path):
    if cat_df.empty:
        raise RuntimeError("No BTFR points available after filtering")
    x = np.log10(cat_df["mbar"].values)
    y = 4.0 * np.log10(cat_df["vflat"].values)
    b = np.median(y - x)
    x_span = np.array([x.min(), x.max()])
    fig, ax = plt.subplots(figsize=(4.6, 3.2))
    ax.scatter(x, y, s=12, alpha=0.7, label="SPARC (fixed $Υ$)")
    ax.plot(x_span, x_span + b, color="C1", lw=2, label=f"slope 1, b={b:.3f} dex")
    ax.plot(x_span, x_span + b + 0.1, color="C1", ls="--", lw=1, label="±0.1 dex")
    ax.plot(x_span, x_span + b - 0.1, color="C1", ls="--", lw=1)
    ax.set_xlabel(r"$\log_{10} M_{\rm bar}\,[M_\odot]$")
    ax.set_ylabel(r"$\log_{10} v_{\rm flat}^4\,[{\rm km}^4\,{\rm s}^{-4}]$")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)
    return b


def make_rotcurve_grid(df_stats: pd.DataFrame, err_floor: float, c_fixed: float | None,
                       fig_path: Path, examples: int = 6):
    if df_stats.empty:
        raise RuntimeError("No rotation-curve statistics available")
    subset = df_stats.sort_values("delta_aicc").head(examples)
    fig, axes = plt.subplots(3, 2, figsize=(7.2, 9.2), sharex=False)
    axes_flat = axes.flatten()
    for ax in axes_flat[len(subset):]:
        ax.axis('off')
    for ax, (_, row) in zip(axes_flat, subset.iterrows()):
        gal = row["galaxy"]
        path = DATA_DIR / f"{gal}_rotmod.dat"
        if not path.exists():
            ax.set_visible(False)
            continue
        r, vobs, eobs, vgas, vdisk, vbul = load_rotmod(path)
        e = np.maximum(eobs, err_floor)
        vbar2 = vbar_sq(vgas, vdisk, vbul)
        model_fdb = np.sqrt(vbar2 + row["v0"]**2)
        c_nfw = row["c_nfw"] if row["c_nfw"] is not None else (c_fixed if c_fixed is not None else 10.0)
        v200 = row["v200_nfw"] if row["v200_nfw"] is not None else 150.0
        vhalo = nfw_vcirc(r, c_nfw, v200)
        model_nfw = np.sqrt(vbar2 + vhalo**2)
        ax.errorbar(r, vobs, yerr=e, fmt='o', ms=3.5, alpha=0.7, label='Obs')
        ax.plot(r, np.sqrt(vbar2), ls='--', color='0.5', label='Newton')
        ax.plot(r, model_fdb, color='C0', lw=2, label='FDB')
        ax.plot(r, model_nfw, color='C1', lw=1.5, ls=':', label='NFW')
        ax.set_title(f"{gal} (ΔAICc={row['delta_aicc']:.1f})", fontsize=9)
        ax.set_xlabel('r [kpc]')
        ax.set_ylabel('v [km s$^{-1}$]')
        ax.grid(alpha=0.3)
    handles, labels = axes_flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', ncol=4, fontsize=8)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, dpi=250)
    plt.close(fig)


def main(err_floor: float = ERR_FLOOR, c_fixed: float | None = None, y_disk: float = 0.5, y_bulge: float = 0.7):
    global Y_DISK, Y_BULGE
    Y_DISK = y_disk
    Y_BULGE = y_bulge
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(DATA_DIR.glob("*_rotmod.dat")):
        gal = path.stem.replace("_rotmod", "")
        r, vobs, eobs, vgas, vdisk, vbul = load_rotmod(path)
        e = np.maximum(eobs, err_floor)
        vbar2 = vbar_sq(vgas, vdisk, vbul)
        n = len(r)
        v0, chi_fdb = fit_fdb(r, vobs, e, vbar2)
        aicc_fdb = aicc(chi_fdb, k=1, n=n)
        c_nfw, v200_nfw, chi_nfw = fit_nfw(r, vobs, e, vbar2, c_fixed=c_fixed)
        k_nfw = 1 if c_fixed is not None else 2
        aicc_nfw = aicc(chi_nfw, k=k_nfw, n=n)
        delta = aicc_fdb - aicc_nfw
        rd_proxy = r.mean()/3 if r.size>0 else 1.0
        vflat = vflat_median(r, vobs, rd=rd_proxy)
        mask_outer = r >= 2.5 * rd_proxy
        if mask_outer.sum() >= 5:
            r_o, vobs_o, e_o = r[mask_outer], vobs[mask_outer], e[mask_outer]
            vbar2_o = vbar2[mask_outer]
            v0_o, chi_fdb_o = fit_fdb(r_o, vobs_o, e_o, vbar2_o)
            aicc_fdb_o = aicc(chi_fdb_o, k=1, n=len(r_o))
            _, _, chi_nfw_o = fit_nfw(r_o, vobs_o, e_o, vbar2_o, c_fixed=c_fixed)
            aicc_nfw_o = aicc(chi_nfw_o, k=k_nfw, n=len(r_o))
            delta_outer = aicc_fdb_o - aicc_nfw_o
        else:
            delta_outer = np.nan
        slope = slope_delta_v2(r, vobs, vbar2, e)
        rows.append(dict(galaxy=gal, n=n, v0=v0, chi2_fdb=chi_fdb, aicc_fdb=aicc_fdb,
                         c_nfw=c_nfw, v200_nfw=v200_nfw, chi2_nfw=chi_nfw, aicc_nfw=aicc_nfw,
                         delta_aicc=delta, delta_aicc_outer=delta_outer,
                         vflat=vflat, slope_dv2=slope))
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    # BTFR plot using catalog masses & V_flat
    btfr_df = load_btfr_catalog(MRT_FILE, Y_DISK)
    b = make_btfr_figure(btfr_df, FIG_BTFR)
    print(f"BTFR intercept b={b:.3f} dex ({len(btfr_df)} galaxies)")

    # Rotation-curve grid of the six most FDB-favored galaxies
    try:
        make_rotcurve_grid(df, err_floor, c_fixed, FIG_ROT_GRID, examples=6)
    except Exception as exc:
        print(f"Warning: failed to build rotation-curve grid: {exc}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--err-floor", type=float, default=ERR_FLOOR)
    p.add_argument("--c-fixed", type=float, default=None)
    p.add_argument("--mldisk", type=float, default=Y_DISK)
    p.add_argument("--mlbulge", type=float, default=Y_BULGE)
    args = p.parse_args()
    main(err_floor=args.err_floor, c_fixed=args.c_fixed, y_disk=args.mldisk, y_bulge=args.mlbulge)
