#!/usr/bin/env python3
# === Two‑Soliton Simulation (V1 style, conformal fields) ===
#
# Goal: visualize the conformal-time evolution of a *single* Maxwell solution
# built from the superposition of two exact Bateman-constructed null fields:
# - material soliton A: "advanced Hopfion-like" (time-reversed) with (p,q)=(1,3)
# - information soliton B: "retarded Hopfion" with (p,q)=(1,1), rotated to propagate from +x to 0
#
# Output: GIF only (z=0 slice of the 3D fields).

from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.gridspec import GridSpec

from hopfion import HopfionSpec, hopfion_fields, rotation_propagate_z_to_minus_x


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


# ==============================
# Output
# ==============================
OUT_DIR = _repo_root() / "out" / "2-soliton"
out_gif = OUT_DIR / "two_soliton_V1_hopfion_z0_120f.gif"

# ==============================
# Time parameters (conformal time)
# ==============================
N_FRAMES = 120
eta_end = 32.0
c = 1.0

# ==============================
# Spatial domain (V1 style)
# ==============================
L = 10.0
nx_bg = 110  # background grid (x,y)
nx_sl = 24  # streamline grid

x = np.linspace(-L, L, nx_bg)
y = np.linspace(-L, L, nx_bg)
X, Y = np.meshgrid(x, y)
Z0 = np.zeros_like(X)

xs = np.linspace(-L, L, nx_sl)
ys = np.linspace(-L, L, nx_sl)
Xs, Ys = np.meshgrid(xs, ys)
Zs0 = np.zeros_like(Xs)

# ==============================
# Two-soliton configuration
# ==============================
d = 8.0  # initial separation along +x for the incoming info soliton
eta_star = d / c  # nominal "encounter time" marker (for annotation only)

MATTER = HopfionSpec(
    p=1,
    q=3,
    kind="advanced",
    center=(0.0, 0.0, 0.0),
    time_shift=0.0,
    rot=None,
)

INFO = HopfionSpec(
    p=1,
    q=1,
    kind="retarded",
    center=(d, 0.0, 0.0),
    time_shift=0.0,
    rot=rotation_propagate_z_to_minus_x(),
)


def total_fields_conformal_z0(eta: float):
    Em = hopfion_fields(eta, X, Y, Z0, MATTER)
    Ei = hopfion_fields(eta, X, Y, Z0, INFO)
    Ex = Em[0] + Ei[0]
    Ey = Em[1] + Ei[1]
    Ez = Em[2] + Ei[2]
    Bx = Em[3] + Ei[3]
    By = Em[4] + Ei[4]
    Bz = Em[5] + Ei[5]
    return Ex, Ey, Ez, Bx, By, Bz


def total_fields_stream_z0(eta: float):
    Em = hopfion_fields(eta, Xs, Ys, Zs0, MATTER)
    Ei = hopfion_fields(eta, Xs, Ys, Zs0, INFO)
    Ex = Em[0] + Ei[0]
    Ey = Em[1] + Ei[1]
    Bx = Em[3] + Ei[3]
    By = Em[4] + Ei[4]
    return Ex, Ey, Bx, By


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    etas = np.linspace(0.0, eta_end, N_FRAMES)

    # fixed color scales over the whole run
    maxE = 0.0
    maxB = 0.0
    for eta in etas:
        Ex, Ey, Ez, Bx, By, Bz = total_fields_conformal_z0(float(eta))
        maxE = max(maxE, float(np.sqrt(Ex * Ex + Ey * Ey + Ez * Ez).max()))
        maxB = max(maxB, float(np.sqrt(Bx * Bx + By * By + Bz * Bz).max()))

    vmaxE = maxE * 1.02
    vmaxB = maxB * 1.02

    with imageio.get_writer(
        out_gif, mode="I", duration=0.09, loop=0, palettesize=64, subrectangles=True
    ) as writer:
        for eta in etas:
            eta = float(eta)
            Ex, Ey, Ez, Bx, By, Bz = total_fields_conformal_z0(eta)
            magE = np.sqrt(Ex * Ex + Ey * Ey + Ez * Ez)
            magB = np.sqrt(Bx * Bx + By * By + Bz * Bz)
            Exs, Eys, Bxs, Bys = total_fields_stream_z0(eta)

            fig = plt.figure(figsize=(10.6, 4.2), dpi=45, facecolor="black")
            gs = GridSpec(1, 4, width_ratios=[1, 0.04, 1, 0.04], wspace=0.18)

            axE = fig.add_subplot(gs[0, 0], facecolor="black")
            caxE = fig.add_subplot(gs[0, 1])
            axB = fig.add_subplot(gs[0, 2], facecolor="black")
            caxB = fig.add_subplot(gs[0, 3])

            imE = axE.imshow(
                magE,
                extent=[-L, L, -L, L],
                origin="lower",
                vmin=0,
                vmax=vmaxE,
                cmap="viridis",
            )
            axE.streamplot(xs, ys, Exs, Eys, color="red", density=0.55, linewidth=0.7)
            fig.colorbar(imE, cax=caxE).set_label("|E| (conformal)")

            imB = axB.imshow(
                magB,
                extent=[-L, L, -L, L],
                origin="lower",
                vmin=0,
                vmax=vmaxB,
                cmap="viridis",
            )
            axB.streamplot(xs, ys, Bxs, Bys, color="cyan", density=0.55, linewidth=0.7)
            fig.colorbar(imB, cax=caxB).set_label("|B| (conformal)")

            for ax in (axE, axB):
                ax.set_xlim(-L, L)
                ax.set_ylim(-L, L)
                ax.set_aspect("equal")
                ax.set_xlabel("x")
                ax.set_ylabel("y")
                ax.plot(0, 0, "wo", markersize=5, label="matter center")
                ax.plot(d, 0, marker="*", color="white", markersize=7, label="info start")

            fig.suptitle(
                "Two Bateman null fields (conformal Maxwell), z=0 slice  "
                f"η={eta:0.2f}  (η★≈{eta_star:0.2f})  "
                f"matter(p,q)=({MATTER.p},{MATTER.q},{MATTER.kind})  "
                f"info(p,q)=({INFO.p},{INFO.q},{INFO.kind})",
                color="white",
                y=0.98,
                fontsize=9,
            )

            canvas = FigureCanvas(fig)
            canvas.draw()
            # Matplotlib 3.8+: tostring_rgb is deprecated but still works; keep for now.
            img = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
            img = img.reshape(canvas.get_width_height()[::-1] + (3,))
            writer.append_data(img)
            plt.close(fig)

    print(f"Saved to {out_gif}")


if __name__ == "__main__":
    main()
