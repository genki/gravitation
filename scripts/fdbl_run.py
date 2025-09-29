#!/usr/bin/env python3
# 最小CLI: 入力PNG/CSVからj_EMを読みYukawa解を計算しSVG出力

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from src.models.fdbl import (
    solve_phi_yukawa_2d,
    grad_from_phi,
)


def load_j(path: Path) -> np.ndarray:
    if path.suffix.lower() == ".csv":
        return np.loadtxt(path, delimiter=",")
    # 画像は輝度をj_EMとみなす
    img = Image.open(path).convert("L")
    arr = np.asarray(img, dtype=float) / 255.0
    return arr


def save_svg(phi: np.ndarray, out: Path) -> None:
    pv = phi - float(np.nanmin(phi))
    pv = pv / (float(np.nanmax(pv)) + 1e-12)
    ny, nx = pv.shape
    W, H = 24 * nx / 2, 24 * ny / 2
    rw, rh = W / nx, H / ny
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W:.0f}" height="{H:.0f}">'
    ]
    for iy in range(ny):
        for ix in range(nx):
            v = int(255 * (1.0 - pv[iy, ix]))
            lines.append(
                f'<rect x="{ix * rw:.2f}" y="{iy * rh:.2f}" '
                f'width="{rw:.2f}" height="{rh:.2f}" '
                f'fill="rgb({v},{v},{v})" />'
            )
    lines.append("</svg>")
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="PNG/CSVのj_EM入力")
    ap.add_argument("--pix", type=float, default=0.2,
                    help="kpc/pix (default: 0.2)")
    ap.add_argument("--lam", type=float, default=5.0,
                    help="λ[kpc] (default: 5.0)")
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--eta", type=float, default=1.0)
    ap.add_argument("--out", type=Path, default=Path("phi.svg"))
    args = ap.parse_args()

    j = load_j(args.input)
    phi = solve_phi_yukawa_2d(j, args.pix, args.lam, args.beta)
    # 触っておく(将来の拡張、未使用抑制)
    _ = grad_from_phi(phi, args.pix)
    save_svg(phi, args.out)
    print(f"saved: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

