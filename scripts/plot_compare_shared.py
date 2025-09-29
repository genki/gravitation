#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font

from src.fdb.sparc import load_sparc_rotmod
from src.fdb.models import gr_baryon_velocity, fdb3_velocity
from src.fdb.utils import sanitize_radial_series


def read_summary(p: Path):
    vals = {}
    with open(p, "r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for k, v in r:
            vals[k] = float(v)
    return vals


def read_ml(p: Path):
    ml = {}
    with open(p, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for d in r:
            ml[d["name"]] = (
                float(d["ml_disk"]),
                float(d["ml_bul"]),
            )
    return ml


def plot_one(name: str, base: Path, outd: Path,
             a: float, b: float, c: float,
             ml_disk: float, ml_bul: float) -> Path:
    rot = load_sparc_rotmod(base / f"{name}_rotmod.dat")
    r_obs, v_obs = sanitize_radial_series(rot.r_kpc, rot.vobs)
    e_obs = rot.everr[: v_obs.size]
    vgr = gr_baryon_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                             ml_disk, ml_bul)
    vf3 = fdb3_velocity(rot.r_kpc, rot.vgas, rot.vdisk, rot.vbul,
                        a, b, c, ml_disk, ml_bul)
    fig, ax = plt.subplots(figsize=(4.8, 3.0), dpi=160)
    ax.errorbar(r_obs, v_obs, yerr=e_obs, fmt='o', ms=3, lw=0.8,
                color='#444', ecolor='#888', label='Vobs')
    ax.plot(rot.r_kpc, vgr, '-', lw=1.2, label='GR(noDM)')
    ax.plot(rot.r_kpc, vf3, '-', lw=1.6, label='FDB3(shared)')
    ax.set_xlabel('R [kpc]')
    ax.set_ylabel('V [km/s]')
    ax.set_title(f'{name} (shared a,b,c)')
    ax.grid(True, ls=':', lw=0.5)
    ax.legend(fontsize=8, frameon=False)
    outd.mkdir(parents=True, exist_ok=True)
    out_svg = outd / f"compare_fit_{name}_shared.svg"
    out_png = outd / f"compare_fit_{name}_shared.png"
    fig.tight_layout()
    fig.savefig(out_svg)
    fig.savefig(out_png, dpi=200)
    plt.close(fig)
    return out_svg


def main():
    use_jp_font()
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='*', default=['DDO154'])
    args = ap.parse_args()
    base = Path('data/sparc/sparc_database')
    outd = Path('assets/figures')
    sm = read_summary(Path('assets/results/global_fit_summary.csv'))
    ml = read_ml(Path('assets/results/global_fit_ml.csv'))
    a, b, c = sm['a'], sm['b'], sm['c']
    for n in args.names:
        if n not in ml:
            print('ML not found for', n)
            continue
        md, mb = ml[n]
        p = plot_one(n, base, outd, a, b, c, md, mb)
        print('saved', p)


if __name__ == '__main__':
    main()
