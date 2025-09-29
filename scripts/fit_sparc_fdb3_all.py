#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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


def fit(rot):
    # GR
    def r_gr(p):
        vhat = gr_baryon_velocity(rot.r_kpc, rot.vgas, rot.vdisk,
                                  rot.vbul, p[0], p[1])
        return (vhat - rot.vobs) / np.maximum(rot.everr, 1.0)

    gr = least_squares(r_gr, np.array([0.5, 0.7]),
                       bounds=(np.array([0.0, 0.0]),
                               np.array([1.5, 2.0])))
    vgr = gr_baryon_velocity(rot.r_kpc, rot.vgas, rot.vdisk,
                              rot.vbul, *gr.x)
    rc_gr = redchi2(rot.vobs, vgr, rot.everr, rot.r_kpc.size - 2)

    # FDB3
    def r_f3(p):
        vhat = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                             p[0], p[1], p[2], p[3], p[4])
        return (vhat - rot.vobs) / np.maximum(rot.everr, 1.0)

    f3 = least_squares(r_f3, np.array([200.0, 3.0, 1.0, 0.5, 0.7]),
                       bounds=(np.array([0.0, 0.1, 0.2, 0.0, 0.0]),
                               np.array([5e4, 50.0, 3.0, 1.5, 2.0])))
    vf3 = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                        *f3.x)
    rc_f3 = redchi2(rot.vobs, vf3, rot.everr, rot.r_kpc.size - 5)

    return rc_gr, rc_f3


def main():
    base = Path("data/sparc/sparc_database")
    outd = Path("assets/results")
    outd.mkdir(parents=True, exist_ok=True)
    files = sorted(base.glob("*_rotmod.dat"))
    if not files:
        print("rotmodファイルが見つかりません。scripts/fetch_sparc.sh")
        print("で取得してください。")
        return

    stats = []
    for p in files:
        rot = load_sparc_rotmod(p)
        try:
            rc_gr, rc_f3 = fit(rot)
        except Exception as e:
            print(f"[SKIP] {rot.name}: {e}")
            continue
        imp = rc_gr / max(rc_f3, 1e-9)
        stats.append((rot.name, rc_gr, rc_f3, imp))
        print(
            f"{rot.name:>12s}  redχ² GR={rc_gr:7.2f}  FDB3={rc_f3:7.2f}  "
            f"x{imp:5.2f}"
        )

    # 保存
    import csv
    with open(outd / "fdb3_per_galaxy.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["name", "redchi2_gr", "redchi2_fdb3", "improve"])
        for n, g, f3, im in stats:
            w.writerow([n, f"{g:.6f}", f"{f3:.6f}", f"{im:.6f}"])

    arr = np.array([[x[1], x[2], x[3]] for x in stats])
    med_imp = np.median(arr[:, 2]) if len(arr) else np.nan
    mean_imp = np.mean(arr[:, 2]) if len(arr) else np.nan
    print("---")
    print(f"銀河数: {len(stats)}  改善中央値x{med_imp:.2f}  平均x{mean_imp:.2f}")


if __name__ == "__main__":
    main()
