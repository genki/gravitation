#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPARCの *_rotmod.dat から NGC3198 等を読み込み、
GR(no DM) と FDB3 を最小二乗で当てはめ、赤字二乗を比較する。

行幅80桁制約を守る。
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from src.fdb.sparc import load_sparc_rotmod
from src.fdb.models import gr_baryon_velocity, fdb3_velocity


def redchi2(y, yhat, err, dof):
    w = np.where(err > 0, 1.0 / (err ** 2.0), 0.0)
    chi2 = np.sum((y - yhat) ** 2.0 * w)
    return chi2 / max(dof, 1)


def fit_gr(rot):
    def resid(p):
        ml_d, ml_b = p
        vhat = gr_baryon_velocity(rot.r_kpc, rot.vgas, rot.vdisk,
                                  rot.vbul, ml_d, ml_b)
        return (vhat - rot.vobs) / np.maximum(rot.everr, 1.0)

    x0 = np.array([0.5, 0.7])
    lb = np.array([0.0, 0.0])
    ub = np.array([1.5, 2.0])
    res = least_squares(resid, x0, bounds=(lb, ub))
    ml_d, ml_b = res.x
    vhat = gr_baryon_velocity(rot.r_kpc, rot.vgas, rot.vdisk,
                              rot.vbul, ml_d, ml_b)
    dof = rot.r_kpc.size - res.x.size
    rchi = redchi2(rot.vobs, vhat, rot.everr, dof)
    return {"pars": (ml_d, ml_b), "vhat": vhat, "redchi2": rchi}


def fit_fdb3(rot):
    def resid(p):
        a, b, c, ml_d, ml_b = p
        vhat = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                             a, b, c, ml_d, ml_b)
        return (vhat - rot.vobs) / np.maximum(rot.everr, 1.0)

    x0 = np.array([200.0, 3.0, 1.0, 0.5, 0.7])
    lb = np.array([0.0, 0.1, 0.2, 0.0, 0.0])
    ub = np.array([5e4, 50.0, 3.0, 1.5, 2.0])
    res = least_squares(resid, x0, bounds=(lb, ub))
    a, b, c, ml_d, ml_b = res.x
    vhat = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                         a, b, c, ml_d, ml_b)
    dof = rot.r_kpc.size - res.x.size
    rchi = redchi2(rot.vobs, vhat, rot.everr, dof)
    return {
        "pars": (a, b, c, ml_d, ml_b),
        "vhat": vhat,
        "redchi2": rchi,
    }


def main():
    base = Path("data/sparc/sparc_database")
    targets = ["NGC3198", "NGC2403"]
    files = [base / f"{t}_rotmod.dat" for t in targets]
    miss = [str(p) for p in files if not p.exists()]
    if miss:
        print("欠損ファイルがあります。取得を確認してください:")
        for m in miss:
            print("  -", m)
        return

    for p in files:
        rot = load_sparc_rotmod(p)
        gr = fit_gr(rot)
        f3 = fit_fdb3(rot)
        print(f"=== {rot.name}  Dist={rot.dist_mpc:.2f} Mpc ===")
        print(
            "GR(noDM)  redχ²=%.2f  ml_d=%.2f  ml_b=%.2f"
            % (gr["redchi2"], gr["pars"][0], gr["pars"][1])
        )
        a, b, c, ml_d, ml_b = f3["pars"]
        print(
            "FDB3      redχ²=%.2f  a=%.1f  b=%.2f  c=%.2f  "
            "ml_d=%.2f ml_b=%.2f"
            % (f3["redchi2"], a, b, c, ml_d, ml_b)
        )
        imp = gr["redchi2"] / max(f3["redchi2"], 1e-9)
        print("improvement x%.2f" % imp)


if __name__ == "__main__":
    main()

