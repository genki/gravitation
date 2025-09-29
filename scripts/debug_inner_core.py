#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

from src.fdb.sparc import load_sparc_rotmod
from src.fdb.models import gr_baryon_velocity, fdb3_velocity


def fit(rot):
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
    return res.x


def main():
    for name in ["DDO154", "DDO161"]:
        rot = load_sparc_rotmod(
            Path("data/sparc/sparc_database") / f"{name}_rotmod.dat"
        )
        pars = fit(rot)
        vgr = gr_baryon_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                                 pars[3], pars[4])
        vf3 = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                            *pars)
        print("==", name, "==")
        for i in range(min(6, rot.r_kpc.size)):
            r = rot.r_kpc[i]
            print(
                f"r={r:.2f}  Vobs={rot.vobs[i]:.2f}±{rot.everr[i]:.2f}  "
                f"Vgr={vgr[i]:.2f}  Vfdb3={vf3[i]:.2f}"
            )


if __name__ == "__main__":
    main()

