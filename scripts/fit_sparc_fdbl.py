#!/usr/bin/env python3
# SPARCのMassModels.mrtから1銀河を選び、ULW-EM(2D軸対称)で
# (lam, A)をグリッド探索して回転曲線を最小二乗フィットする。

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import numpy as np

from src.models.fdbl import (
    solve_phi_yukawa_2d,
    grad_from_phi,
    circular_profile,
)


@dataclass
class SparcRC:
    name: str
    R: np.ndarray  # kpc
    Vobs: np.ndarray  # km/s
    eV: np.ndarray  # km/s
    Vgas: np.ndarray  # km/s
    Vdisk: np.ndarray  # km/s
    Vbul: np.ndarray  # km/s
    SBdisk: np.ndarray  # Lsun/pc^2


@dataclass
class SparcMeta:
    name: str
    T: int | None
    D_mpc: float | None
    Inc_deg: float | None
    L36_1e9Lsun: float | None
    Rdisk_kpc: float | None
    SBdisk0_Lsunpc2: float | None
    MHI_1e9Msun: float | None
    RHI_kpc: float | None
    Vflat_kms: float | None
    Q: int | None


def read_sparc_meta(path: Path, name: str) -> SparcMeta | None:
    """Parse SPARC Table1 lines by splitting tokens after the Galaxy name.

    Columns (after Galaxy): T, D, e_D, f_D, Inc, e_Inc, L36, e_L36,
    Reff, SBeff, Rdisk, SBdisk, MHI, RHI, Vflat, e_Vflat, Q, Ref.
    """
    try:
        for ln in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = ln.strip()
            if (not s or s.startswith("Title") or s.startswith("Authors") or
                    s.startswith("Table") or s.startswith("Byte") or s.startswith("Note") or
                    set(s) in ({'-'}, {'='})):
                continue
            gal = ln[0:11].strip()
            if gal != name:
                continue
            rest = ln[11:].strip().split()
            # guard
            if len(rest) < 17:
                return SparcMeta(name=gal, T=None, D_mpc=None, Inc_deg=None,
                                 L36_1e9Lsun=None, Rdisk_kpc=None,
                                 SBdisk0_Lsunpc2=None, MHI_1e9Msun=None,
                                 RHI_kpc=None, Vflat_kms=None, Q=None)
            def f(i):
                try:
                    return float(rest[i])
                except Exception:
                    return None
            def ii(i):
                try:
                    return int(rest[i])
                except Exception:
                    return None
            T = ii(0)
            D = f(1)
            Inc = f(4)
            L36 = f(6)
            Rd = f(10)
            SBd0 = f(11)
            MHI = f(12)
            RHI = f(13)
            Vflat = f(14)
            Q = ii(16)
            return SparcMeta(name=gal, T=T, D_mpc=D, Inc_deg=Inc, L36_1e9Lsun=L36,
                             Rdisk_kpc=Rd, SBdisk0_Lsunpc2=SBd0, MHI_1e9Msun=MHI,
                             RHI_kpc=RHI, Vflat_kms=Vflat, Q=Q)
    except Exception:
        return None
    return None


def read_sparc_massmodels(path: Path, name: str) -> SparcRC:
    R = []
    Vobs = []
    eV = []
    Vgas = []
    Vdisk = []
    Vbul = []
    SBd = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line or line.startswith("=") or line.startswith("-"):
                continue
            if line.strip().startswith("Title") or line.strip().startswith(
                "Byte-by-byte"
            ):
                continue
            gal = line[0:11].strip()
            if gal != name:
                continue
            try:
                # 可変幅: 先頭の銀河名以降を分割
                rest = line[11:].strip().split()
                # D, R, Vobs, eVobs, Vgas, Vdisk, Vbul, SBdisk, SBbul
                _, r, vobs, ev, vgas, vdisk, vbul, sbd, *_ = rest + ["0"]
                r = float(r)
                vobs = float(vobs)
                ev = float(ev)
                vgas = float(vgas)
                vdisk = float(vdisk)
                vbul = float(vbul)
                sbd = float(sbd)
            except Exception:
                continue
            R.append(r)
            Vobs.append(vobs)
            eV.append(ev if ev > 0 else 5.0)
            Vgas.append(vgas)
            Vdisk.append(vdisk)
            Vbul.append(vbul)
            SBd.append(max(sbd, 0.0))
    if not R:
        raise SystemExit(f"Galaxy '{name}' not found in {path}")
    arr = lambda x: np.asarray(x, dtype=float)
    return SparcRC(
        name=name,
        R=arr(R),
        Vobs=arr(Vobs),
        eV=arr(eV),
        Vgas=arr(Vgas),
        Vdisk=arr(Vdisk),
        Vbul=arr(Vbul),
        SBdisk=arr(SBd),
    )


def make_axisymmetric_image(
    R_kpc: np.ndarray,
    SBdisk: np.ndarray,
    pix_kpc: float,
    size: int = 256,
) -> np.ndarray:
    """半径プロファイルSBdisk(R)から軸対称j_EM画像を生成する。"""
    ny = nx = size
    y = (np.arange(ny) - (ny - 1) / 2.0) * pix_kpc
    x = (np.arange(nx) - (nx - 1) / 2.0) * pix_kpc
    yy, xx = np.meshgrid(y, x, indexing="ij")
    r = np.hypot(xx, yy)
    # Rが単調でない可能性は小さいが、外挿は端値に丸める
    j_r = np.interp(r.ravel(), R_kpc, SBdisk, left=SBdisk[0], right=SBdisk[-1])
    j = j_r.reshape(ny, nx)
    # スケールを正規化（最大1）
    m = np.nanmax(j)
    if m > 0:
        j = j / m
    return j


def model_velocity(
    rc: SparcRC,
    lam_kpc: float,
    A: float,
    pix_kpc: float,
    size: int = 256,
) -> Tuple[np.ndarray, np.ndarray]:
    # 軸対称jを構築
    j = make_axisymmetric_image(rc.R, rc.SBdisk, pix_kpc=pix_kpc, size=size)
    phi = solve_phi_yukawa_2d(j, pix_kpc=pix_kpc, lam_kpc=lam_kpc, beta=1.0)
    dpx, dpy = grad_from_phi(phi, pix_kpc=pix_kpc)
    gx = -A * dpx
    gy = -A * dpy
    rgrid, gr = circular_profile(gx, gy, pix_kpc=pix_kpc, nbins=64)
    # 観測Rに補間
    g_ulw = np.interp(rc.R, rgrid, gr, left=np.nan, right=np.nan)
    # GR(no DM): Vb^2 = Vgas^2 + Vdisk^2 + Vbul^2
    Vb2 = rc.Vgas**2 + rc.Vdisk**2 + rc.Vbul**2
    g_gr = Vb2 / np.maximum(rc.R, 1e-6)
    v_model = np.sqrt(np.clip((g_gr + g_ulw) * rc.R, 0.0, None))
    return v_model, g_ulw


def chi2(v_model: np.ndarray, rc: SparcRC) -> float:
    w = 1.0 / np.maximum(rc.eV, 5.0)
    return float(np.nansum(((v_model - rc.Vobs) * w) ** 2))


def grid_search(
    rc: SparcRC,
    pix_kpc: float = 0.2,
    size: int = 256,
) -> Tuple[float, float, float]:
    best = (np.inf, np.nan, np.nan)
    for lam in (2.0, 3.0, 5.0, 8.0, 12.0):
        for A in np.logspace(-2, 2, 9):
            v, _ = model_velocity(rc, lam, A, pix_kpc, size)
            c2 = chi2(v, rc)
            if c2 < best[0]:
                best = (c2, lam, A)
    return best[1], best[2], best[0]


def svg_curve(rc: SparcRC, v: np.ndarray, lam: float, A: float) -> str:
    W, H = 640, 360
    pad = 40
    xmin, xmax = 0.0, float(np.nanmax(rc.R) * 1.05)
    ymin, ymax = 0.0, float(max(np.nanmax(rc.Vobs), np.nanmax(v)) * 1.1)

    def xmap(x):
        return pad + (W - 2 * pad) * (x - xmin) / (xmax - xmin + 1e-12)

    def ymap(y):
        return H - pad - (H - 2 * pad) * (y - ymin) / (ymax - ymin + 1e-12)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}"'
        f' height="{H}">',
        '<style>text{font-family:system-ui;font-size:12px}</style>',
        f'<text x="{pad}" y="20">{rc.name}: lam={lam:.2f}kpc, '
        f'A={A:.3g}</text>',
        # axes
        f'<line x1="{pad}" y1="{H-pad}" x2="{W-pad}" y2="{H-pad}" '
        'stroke="#444"/>',
        f'<line x1="{pad}" y1="{pad}" x2="{pad}" y2="{H-pad}" '
        'stroke="#444"/>',
    ]
    # Observed data + error bars
    for R, y, e in zip(rc.R, rc.Vobs, rc.eV):
        x = xmap(R)
        yy = ymap(y)
        e0, e1 = ymap(y - e), ymap(y + e)
        parts.append(
            f'<line x1="{x:.2f}" y1="{e0:.2f}" x2="{x:.2f}" '
            f'y2="{e1:.2f}" stroke="#888"/>'
        )
        parts.append(
            f'<circle cx="{x:.2f}" cy="{yy:.2f}" r="2.2" '
            'fill="#222" />'
        )
    # Model curve
    path = "M " + " ".join(
        f"{xmap(R):.2f},{ymap(yy):.2f}" for R, yy in zip(rc.R, v)
        if np.isfinite(yy)
    )
    parts.append(
        f'<path d="{path}" fill="none" stroke="#1f77b4" '
        'stroke-width="2" />'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name", help="SPARCの銀河名(例: DDO154)")
    ap.add_argument("--mrt", type=Path,
                    default=Path("data/sparc/MassModels_Lelli2016c.mrt"))
    ap.add_argument("--pix", type=float, default=0.2)
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--out", type=Path,
                    default=Path("paper/figures/sparc_fit.svg"))
    args = ap.parse_args()

    rc = read_sparc_massmodels(args.mrt, args.name)
    lam, A, c2 = grid_search(rc, pix_kpc=args.pix, size=args.size)
    v, _ = model_velocity(rc, lam, A, pix_kpc=args.pix, size=args.size)
    svg = svg_curve(rc, v, lam, A)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg, encoding="utf-8")
    print(f"best lam={lam:.3g} kpc, A={A:.3g}, chi2={c2:.3g}")
    print(f"saved: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
