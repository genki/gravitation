#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from scipy.optimize import least_squares

from src.fdb.sparc import load_sparc_rotmod
from src.fdb.models import gr_baryon_velocity, fdb3_velocity


def ensure_dirs():
    outd = Path("assets/figures")
    outd.mkdir(parents=True, exist_ok=True)
    return outd


def load_stats(csv_path: Path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            rows.append(
                (
                    d["name"],
                    float(d["redchi2_gr"]),
                    float(d["redchi2_fdb3"]),
                    float(d["improve"]),
                )
            )
    return rows


def plot_distributions(rows, outd: Path):
    imp = np.array([x[3] for x in rows])
    fig, ax = plt.subplots(figsize=(5.0, 3.2), dpi=160)
    ax.hist(np.clip(imp, 1e-3, None), bins=40, color="#1f77b4")
    ax.set_xscale("log")
    ax.set_xlabel("improvement factor (redχ²_GR / redχ²_FDB3)")
    ax.set_ylabel("count")
    ax.grid(True, ls=":", lw=0.5)
    fig.tight_layout()
    p1 = outd / "sota_improvement_hist.png"
    fig.savefig(p1)
    plt.close(fig)

    gr = np.array([x[1] for x in rows])
    f3 = np.array([x[2] for x in rows])
    fig, ax = plt.subplots(figsize=(5.0, 3.2), dpi=160)
    ax.scatter(gr, f3, s=8, alpha=0.6)
    lim = [0.8 * min(gr.min(), f3.min()), 1.2 * max(gr.max(), f3.max())]
    ax.plot(lim, lim, "r--", lw=1)
    ax.set_xlabel("redχ² GR(noDM)")
    ax.set_ylabel("redχ² FDB3")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.grid(True, ls=":", lw=0.5)
    fig.tight_layout()
    p2 = outd / "sota_redchi2_scatter.png"
    fig.savefig(p2)
    plt.close(fig)
    return p1, p2


def fit_vr(name: str, base: Path):
    rot = load_sparc_rotmod(base / f"{name}_rotmod.dat")
    def resid(p):
        a, b, c, ml_d, ml_b = p
        vhat = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                             a, b, c, ml_d, ml_b)
        e = np.maximum(rot.everr, 1.0)
        return (vhat - rot.vobs) / e
    x0 = np.array([200.0, 3.0, 1.0, 0.5, 0.7])
    lb = np.array([0.0, 0.1, 0.2, 0.0, 0.0])
    ub = np.array([5e4, 50.0, 3.0, 1.5, 2.0])
    res = least_squares(resid, x0, bounds=(lb, ub))
    pars = res.x
    vgr = gr_baryon_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                             pars[3], pars[4])
    vf3 = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul, *pars)
    return rot, pars, vgr, vf3


def plot_vr_panel(names, outd: Path):
    base = Path("data/sparc/sparc_database")
    n = len(names)
    ncol = 2
    nrow = (n + ncol - 1) // ncol
    fig, axes = plt.subplots(nrow, ncol, figsize=(6.4, 3.2 * nrow), dpi=160)
    axes = np.atleast_2d(axes)
    for i, name in enumerate(names):
        ax = axes[i // ncol, i % ncol]
        rot, pars, vgr, vf3 = fit_vr(name, base)
        ax.errorbar(rot.r_kpc, rot.vobs, yerr=rot.everr, fmt='o', ms=3,
                    lw=0.8, color='#444', ecolor='#888', label='Vobs')
        ax.plot(rot.r_kpc, vgr, '-', lw=1.2, label='GR(noDM)')
        ax.plot(rot.r_kpc, vf3, '-', lw=1.6, label='FDB')
        ax.set_title(f"{name}  a={pars[0]:.1f} b={pars[1]:.2f} c={pars[2]:.2f}")
        ax.set_xlabel('R [kpc]')
        ax.set_ylabel('V [km/s]')
        ax.grid(True, ls=':', lw=0.5)
        if i == 0:
            ax.legend(fontsize=8, frameon=False)
    for j in range(i + 1, nrow * ncol):
        fig.delaxes(axes[j // ncol, j % ncol])
    fig.tight_layout()
    p = outd / "sota_vr_panel.png"
    fig.savefig(p)
    plt.close(fig)
    return p


def main():
    use_jp_font()
    outd = ensure_dirs()
    stats_path = Path("assets/results/fdb3_per_galaxy.csv")
    if not stats_path.exists():
        print("stats not found. Run fit_sparc_fdb3_all.py first.")
        return
    rows = load_stats(stats_path)
    p1, p2 = plot_distributions(rows, outd)
    # 代表銀河: 指定＋悪化例（improve<1）から数件
    names = ["DDO154", "DDO161", "NGC3198", "NGC2403"]
    bad = [r[0] for r in rows if r[3] < 1.0]
    names.extend(bad[:2])
    p3 = plot_vr_panel(names, outd)
    # worstケース: 改善倍率が小さい順に上位（悪化/未改善）を抽出
    rows_sorted = sorted(rows, key=lambda x: x[3])  # improve ascending
    worst_names = [r[0] for r in rows_sorted[:4]]  # 4枚構成
    # 代表と重複する場合を許容（明示的にworst集合を別図に）
    base = Path("data/sparc/sparc_database")
    n = len(worst_names)
    ncol = 2
    nrow = (n + ncol - 1) // ncol
    import numpy as np
    from src.fdb.sparc import load_sparc_rotmod
    from src.fdb.models import gr_baryon_velocity, fdb3_velocity
    def fit_vr(name: str):
        rot = load_sparc_rotmod(base / f"{name}_rotmod.dat")
        from scipy.optimize import least_squares
        def resid(p):
            a, b, c, ml_d, ml_b = p
            vhat = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                                 a, b, c, ml_d, ml_b)
            e = np.maximum(rot.everr, 1.0)
            return (vhat - rot.vobs) / e
        x0 = np.array([200.0, 3.0, 1.0, 0.5, 0.7])
        lb = np.array([0.0, 0.1, 0.2, 0.0, 0.0])
        ub = np.array([5e4, 50.0, 3.0, 1.5, 2.0])
        res = least_squares(resid, x0, bounds=(lb, ub))
        pars = res.x
        vgr = gr_baryon_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                                 pars[3], pars[4])
        vf3 = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul, *pars)
        return rot, pars, vgr, vf3
    fig, axes = plt.subplots(nrow, ncol, figsize=(6.4, 3.2 * nrow), dpi=160)
    axes = np.atleast_2d(axes)
    for i, name in enumerate(worst_names):
        ax = axes[i // ncol, i % ncol]
        rot, pars, vgr, vf3 = fit_vr(name)
        ax.errorbar(rot.r_kpc, rot.vobs, yerr=rot.everr, fmt='o', ms=3,
                    lw=0.8, color='#444', ecolor='#888', label='Vobs')
        ax.plot(rot.r_kpc, vgr, '-', lw=1.2, label='GR(noDM)')
        ax.plot(rot.r_kpc, vf3, '-', lw=1.6, label='FDB')
        ax.set_title(f"{name} (worst)  a={pars[0]:.1f} b={pars[1]:.2f} c={pars[2]:.2f}")
        ax.set_xlabel('R [kpc]')
        ax.set_ylabel('V [km/s]')
        ax.grid(True, ls=':', lw=0.5)
        if i == 0:
            ax.legend(fontsize=8, frameon=False)
    for j in range(i + 1, nrow * ncol):
        fig.delaxes(axes[j // ncol, j % ncol])
    fig.tight_layout()
    p4 = outd / "sota_vr_panel_worst.png"
    fig.savefig(p4)
    plt.close(fig)
    print("saved", p1)
    print("saved", p2)
    print("saved", p3)
    print("saved", p4)


if __name__ == "__main__":
    main()
