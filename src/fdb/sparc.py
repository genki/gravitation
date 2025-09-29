from __future__ import annotations

import dataclasses as dc
from pathlib import Path
from typing import List

import numpy as np


@dc.dataclass
class RotMod:
    name: str
    dist_mpc: float
    r_kpc: np.ndarray
    vobs: np.ndarray
    everr: np.ndarray
    vgas: np.ndarray
    vdisk: np.ndarray
    vbul: np.ndarray


def load_sparc_rotmod(path: Path) -> RotMod:
    """SPARCの *_rotmod.dat を読み込む。"""
    name = path.stem.replace("_rotmod", "")
    dist = 0.0
    rows: List[List[float]] = []
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            if ln.startswith("# Distance"):
                try:
                    dist = float(ln.split("=")[-1].split()[0])
                except Exception:
                    dist = np.nan
                continue
            if ln.startswith("#"):
                continue
            vals = [float(x) for x in ln.split()]
            # Rad, Vobs, errV, Vgas, Vdisk, Vbul,
            # SBdisk, SBbul (SBは未使用)
            rows.append(vals[:6])
    arr = np.asarray(rows, dtype=float)
    r, vobs, everr, vgas, vdisk, vbul = arr.T
    return RotMod(
        name=name,
        dist_mpc=dist,
        r_kpc=r,
        vobs=vobs,
        everr=everr,
        vgas=vgas,
        vdisk=vdisk,
        vbul=vbul,
    )

