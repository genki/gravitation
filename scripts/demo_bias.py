#!/usr/bin/env python3
# SPDX-License-Identifier: internal
# ULW-EM(FDB)デモ: 非対称源で放射状バイアスの直観図を生成(SVG)

from pathlib import Path

import numpy as np

from src.models.fdbl import (
    gaussian_sources,
    solve_phi_yukawa_2d,
    grad_from_phi,
)


def field_arrows(gx: np.ndarray, gy: np.ndarray, step: int,
                 x0: float, y0: float, w: float, h: float) -> str:
    ny, nx = gx.shape
    xs = np.arange(0, nx, step)
    ys = np.arange(0, ny, step)
    rw = w / nx
    rh = h / ny
    out: list[str] = []
    for iy in ys:
        for ix in xs:
            vx = gx[iy, ix]
            vy = gy[iy, ix]
            # 視覚のため正規化
            s = (vx * vx + vy * vy) ** 0.5 + 1e-12
            vx /= s
            vy /= s
            x = x0 + ix * rw
            y = y0 + iy * rh
            x2 = x + 6.0 * vx
            y2 = y - 6.0 * vy
            out.append(
                f'<line x1="{x:.2f}" y1="{y:.2f}" '
                f'x2="{x2:.2f}" y2="{y2:.2f}" '
                f'stroke="#1f77b4" stroke-width="1" />'
            )
    return "\n".join(out)


def main() -> int:
    nx, ny = 192, 192
    pix = 0.2  # kpc/pix
    lam = 5.0  # kpc
    beta = 1.0
    eta = 1.0

    centers = [(-4.0, 0.0), (2.0, 0.0)]  # kpc
    j = gaussian_sources(nx, ny, pix, centers, sigma_kpc=0.8, amp=1.0)
    phi = solve_phi_yukawa_2d(j, pix_kpc=pix, lam_kpc=lam, beta=beta)
    dphix, dphiy = grad_from_phi(phi, pix_kpc=pix)
    gx = -eta * dphix
    gy = -eta * dphiy

    # 可視化用に正規化
    jv = j / (np.nanmax(j) + 1e-12)
    pv = phi - np.nanmin(phi)
    pv = pv / (np.nanmax(pv) + 1e-12)

    # SVG組み立て
    W, H = 640, 300
    svg: list[str] = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
               f'width="{W}" height="{H}">')
    svg.append('<style>text{font-family:system-ui; font-size:14px}</style>')
    # j_EM
    svg.append('<text x="20" y="24">j_EM (sources)</text>')
    ny, nx = jv.shape
    rw = 256 / nx
    rh = 256 / ny
    for iy in range(ny):
        for ix in range(nx):
            v = int(255 * (1.0 - jv[iy, ix]))
            svg.append(
                f'<rect x="{20 + ix * rw:.2f}" y="{36 + iy * rh:.2f}" '
                f'width="{rw:.2f}" height="{rh:.2f}" '
                f'fill="rgb({v},{v},{v})" />'
            )
    # phi + ベクトル
    svg.append('<text x="346" y="24">phi & g field</text>')
    ny, nx = pv.shape
    rw = 256 / nx
    rh = 256 / ny
    for iy in range(ny):
        for ix in range(nx):
            v = int(255 * (1.0 - pv[iy, ix]))
            svg.append(
                f'<rect x="{346 + ix * rw:.2f}" y="{36 + iy * rh:.2f}" '
                f'width="{rw:.2f}" height="{rh:.2f}" '
                f'fill="rgb({v},{v},{v})" />'
            )
    svg.append(field_arrows(gx, gy, step=8, x0=346, y0=36,
                            w=256, h=256))
    svg.append('</svg>')

    outdir = Path("paper/figures")
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "fdbl_bias.svg"
    out.write_text("\n".join(svg), encoding="utf-8")
    print(f"saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

