#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import math
import csv
import json
import random

import numpy as np


def read_2mrs(path: Path):
    rows = []
    with path.open() as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            try:
                ra = float(row["RAJ2000"])
                dec = float(row["DEJ2000"])
                cz = float(row.get("cz", "nan"))
            except Exception:
                continue
            if not math.isfinite(cz):
                continue
            rows.append((ra, dec, cz))
    return rows


def sph2cart(ra_deg, dec_deg, r):
    ra = math.radians(ra_deg)
    dec = math.radians(dec_deg)
    x = r * math.cos(dec) * math.cos(ra)
    y = r * math.cos(dec) * math.sin(ra)
    z = r * math.sin(dec)
    return x, y, z


def cz_to_mpc(cz_kms: float, H0: float = 70.0) -> float:
    return cz_kms / H0


def local_shape_metrics(P: np.ndarray) -> tuple[float, float]:
    # P: (N,3)
    if P.shape[0] < 5:
        return float("nan"), float("nan")
    C = np.cov(P.T)
    w, _ = np.linalg.eigh(C)
    w = np.sort(np.clip(w, 0.0, None))[::-1]
    s = w.sum() + 1e-12
    l1, l2, l3 = w
    F = (l1 - l2) / s
    Pn = (l2 - l3) / s
    return float(F), float(Pn)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cat", type=Path, default=Path("data/lss/2mrs_table3.tsv"))
    ap.add_argument("--zmin", type=float, default=0.005)
    ap.add_argument("--zmax", type=float, default=0.04)
    ap.add_argument("--R", type=float, default=10.0, help="近傍半径[Mpc]")
    ap.add_argument("--nsamp", type=int, default=2000)
    ap.add_argument("--out", type=Path, default=Path("data/results/filamentarity.json"))
    args = ap.parse_args()

    rows = read_2mrs(args.cat)
    pts = []
    for ra, dec, cz in rows:
        z = cz / 3e5
        if not (args.zmin <= z <= args.zmax):
            continue
        r = cz_to_mpc(cz)
        pts.append(sph2cart(ra, dec, r))
    P = np.array(pts, dtype=float)
    N = P.shape[0]
    if N == 0:
        print("no points in selection")
        return 1

    # KD-like brute force by chunks
    idx = random.sample(range(N), min(args.nsamp, N))
    F_list = []
    P_list = []
    R2 = args.R * args.R
    for i in idx:
        d2 = np.sum((P - P[i]) ** 2, axis=1)
        neigh = P[d2 <= R2]
        F, Pl = local_shape_metrics(neigh)
        if math.isfinite(F) and math.isfinite(Pl):
            F_list.append(F)
            P_list.append(Pl)

    F_arr = np.array(F_list)
    P_arr = np.array(P_list)
    res = {
        "N_total": int(N),
        "N_eval": int(len(F_list)),
        "R_Mpc": args.R,
        "z_range": [args.zmin, args.zmax],
        "F_median": float(np.nanmedian(F_arr)),
        "P_median": float(np.nanmedian(P_arr)),
        "F_mean": float(np.nanmean(F_arr)),
        "P_mean": float(np.nanmean(P_arr)),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(res, indent=2), encoding="utf-8")
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

