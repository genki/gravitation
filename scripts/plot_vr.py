#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPARCの銀河(例: DDO154, DDO161)について、V-R図を作成。
観測Vobsと誤差、GR(noDM)、FDB3(最小二乗)を重ね描きし、
中心付近でVが0付近に張り付く見え方を検証・回避する。

出力: assets/figures/vr_<name>.png
"""

from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from scipy.optimize import least_squares

from src.fdb.sparc import load_sparc_rotmod
from src.fdb.models import gr_baryon_velocity, fdb3_velocity
from src.fdb.utils import sanitize_radial_series


def fit_fdb3(rot):
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


def plot_vr(name: str, base: Path) -> Path:
    path = base / f"{name}_rotmod.dat"
    rot = load_sparc_rotmod(path)
    # 観測系列の健全化（万一の原点アンカー除去）
    r_obs, v_obs = sanitize_radial_series(rot.r_kpc, rot.vobs)
    e_obs = rot.everr[: v_obs.size]
    pars = fit_fdb3(rot)
    ml_d, ml_b = pars[3], pars[4]
    vgr = gr_baryon_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                             ml_d, ml_b)
    vf3 = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul, *pars)

    # 描画
    fig, ax = plt.subplots(figsize=(5.0, 3.2), dpi=160)
    ax.errorbar(r_obs, v_obs, yerr=e_obs, fmt='o', ms=3,
                lw=0.8, color='#444', ecolor='#888', label='Vobs')
    ax.plot(rot.r_kpc, vgr, '-', lw=1.2, label='GR(noDM)')
    ax.plot(rot.r_kpc, vf3, '-', lw=1.6, label='FDB3')
    ax.set_xlabel('R [kpc]')
    ax.set_ylabel('V [km/s]')
    ax.set_title(f'{name}  fit: a={pars[0]:.1f} b={pars[1]:.2f} '
                 f'c={pars[2]:.2f} ml_d={ml_d:.2f}')
    ax.grid(True, ls=':', lw=0.5)
    ax.legend(fontsize=8, frameon=False)
    outd = Path('assets/figures')
    outd.mkdir(parents=True, exist_ok=True)
    out = outd / f"vr_{name}.png"
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    use_jp_font()
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='*', default=['DDO154', 'DDO161'])
    args = ap.parse_args()
    base = Path('data/sparc/sparc_database')
    for n in args.names:
        p = plot_vr(n, base)
        print('saved', p)


if __name__ == '__main__':
    main()
