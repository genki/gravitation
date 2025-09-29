#!/usr/bin/env python3
# SPDX-License-Identifier: internal
# ULW-EM(FDB; Future Decoherence Bias)デモ: 依存レスSVG図を生成

from pathlib import Path

import numpy as np

from src.models.fdbl import (
    exponential_disk,
    solve_phi_yukawa_2d,
    grad_from_phi,
    circular_profile,
    vc_from_gr,
)


def to_heat_rects(img: np.ndarray, x0: float, y0: float,
                  w: float, h: float) -> str:
    """img(0-1)を矩形群に変換してSVG断片を返す。"""
    ny, nx = img.shape
    rw = w / nx
    rh = h / ny
    out: list[str] = []
    for iy in range(ny):
        for ix in range(nx):
            v = np.clip(img[iy, ix], 0.0, 1.0)
            c = int(255 * (1.0 - v))  # 白=低, 黒=高
            out.append(
                f'<rect x="{x0 + ix * rw:.2f}" y="{y0 + iy * rh:.2f}" '
                f'width="{rw:.2f}" height="{rh:.2f}" '
                f'fill="rgb({c},{c},{c})" />'
            )
    return "\n".join(out)


def line_path(xs: np.ndarray, ys: np.ndarray,
              x0: float, y0: float, w: float, h: float) -> str:
    """データを枠に線形スケーリングして折れ線パスを返す。"""
    xmn, xmx = float(np.nanmin(xs)), float(np.nanmax(xs))
    ymn, ymx = float(np.nanmin(ys)), float(np.nanmax(ys))
    xsn = (xs - xmn) / (xmx - xmn + 1e-12)
    ysn = (ys - ymn) / (ymx - ymn + 1e-12)
    # SVGはy下向き。上向きにしたいので1-ysn。
    pts = [
        (x0 + w * xsn[i], y0 + h * (1.0 - ysn[i]))
        for i in range(len(xsn))
        if np.isfinite(xsn[i]) and np.isfinite(ysn[i])
    ]
    d = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in pts)
    return f'<path d="{d}" fill="none" stroke="#1f77b4" stroke-width="2" />'


def main() -> int:
    nx, ny = 256, 256
    pix = 0.2  # kpc/pix
    lam = 5.0  # kpc
    beta = 1.0
    eta = 1.0

    j = exponential_disk(nx, ny, pix_kpc=pix, i0=1.0, r_d_kpc=2.5)
    phi = solve_phi_yukawa_2d(j, pix_kpc=pix, lam_kpc=lam, beta=beta)
    dphix, dphiy = grad_from_phi(phi, pix_kpc=pix)
    gx = -eta * dphix
    gy = -eta * dphiy
    r, gr = circular_profile(gx, gy, pix_kpc=pix, nbins=64)
    vc = vc_from_gr(gr, r)

    # 可視化用に64×64へ縮小
    def bin2(a: np.ndarray, bx: int, by: int) -> np.ndarray:
        ny, nx = a.shape
        a = a[: ny - (ny % by), : nx - (nx % bx)]
        ny2, nx2 = a.shape
        a = a.reshape(ny2 // by, by, nx2 // bx, bx).mean(axis=(1, 3))
        return a

    jv = j / (np.nanmax(j) + 1e-12)
    pv = phi - np.nanmin(phi)
    pv = pv / (np.nanmax(pv) + 1e-12)
    j64 = bin2(jv, 4, 4)
    p64 = bin2(pv, 4, 4)

    W, H = 960, 320
    svg: list[str] = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'width="{W}" height="{H}">')
    svg.append('<style>text{font-family:system-ui; font-size:14px}</style>')
    # パネル1: j_EM
    svg.append('<text x="20" y="24">j_EM (arb.)</text>')
    svg.append(to_heat_rects(j64, 20, 36, 256, 256))
    # パネル2: phi
    svg.append('<text x="356" y="24">phi</text>')
    svg.append(to_heat_rects(p64, 356, 36, 256, 256))
    # パネル3: v_c(R)
    svg.append('<text x="692" y="24">v_c (ULW-EM)</text>')
    # 枠
    svg.append('<rect x="692" y="36" width="248" height="256" '
               'fill="none" stroke="#888"/>')
    svg.append(line_path(r, vc, 692, 36, 248, 256))
    svg.append('</svg>')

    outdir = Path("paper/figures")
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "fdbl_demo.svg"
    out.write_text("\n".join(svg), encoding="utf-8")
    print(f"saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
