#!/usr/bin/env python3
# === Two‑Soliton Simulation (V1 exact style) ===
# Material soliton (advanced EM Hopfion) + Info soliton (retarded EM Hopfion)
# Output: GIF only

from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.gridspec import GridSpec

# ==============================
# Output
# ==============================
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "out" / "2-soliton"
out_gif = OUT_DIR / "two_soliton_V1_exact_fixedsim_240f.gif"

# ==============================
# Time parameters (conformal time)
# ==============================
N_FRAMES = 240
eta_star = 8.0  # resonance time
eta_end = 32.0  # includes re-emission phase (2x interval)
c = 1.0

# ==============================
# Spatial domain (V1 style)
# ==============================
L = 10.0
nx_bg = 110  # background grid
nx_sl = 24  # streamline grid

x = np.linspace(-L, L, nx_bg)
y = np.linspace(-L, L, nx_bg)
X, Y = np.meshgrid(x, y)

xs = np.linspace(-L, L, nx_sl)
ys = np.linspace(-L, L, nx_sl)
Xs, Ys = np.meshgrid(xs, ys)

# ==============================
# Matter soliton parameters
# ==============================
h0 = 3  # initial H-index
sigma_m = 1.9
A_m_pre = 1.0
A_m_post = 1.25  # density increase after resonance

# ==============================
# Info soliton parameters
# ==============================
d = 8.0  # initial separation
info_center = (d, 0.0)
A_info0 = 1.1
sigma0 = 0.55
alpha_decay = 1.15  # amplitude dilution
sigma_growth = 0.35  # diffusion
A_reemit0 = 1.0


# ==============================
# Utility functions
# ==============================
def tangential(theta: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return -np.sin(theta), np.cos(theta)


# ==============================
# Field definitions
# ==============================
def matter_fields(XX: np.ndarray, YY: np.ndarray, eta: float):
    n = h0 if eta < eta_star else h0 + 1
    A = A_m_pre if eta < eta_star else A_m_post
    r = np.hypot(XX, YY) + 1e-9
    th = np.arctan2(YY, XX)
    amp = A * np.exp(-((r / sigma_m) ** 2))
    angle = n * th
    tx, ty = tangential(angle)
    Ex = amp * tx
    Ey = amp * ty
    angleB = angle + np.pi / 2
    bx, by = tangential(angleB)
    Bx = 0.95 * amp * bx
    By = 0.95 * amp * by
    return Ex, Ey, Bx, By


def ring_profile(r: np.ndarray, R: float, sigma: float) -> np.ndarray:
    return np.exp(-((r - R) ** 2) / (2 * sigma**2))


def info_incoming_fields(XX: np.ndarray, YY: np.ndarray, eta: float):
    Ex = np.zeros_like(XX)
    Ey = np.zeros_like(YY)
    Bx = np.zeros_like(XX)
    By = np.zeros_like(YY)
    cx, cy = info_center
    dx = XX - cx
    dy = YY - cy
    r = np.hypot(dx, dy) + 1e-9
    th = np.arctan2(dy, dx)
    R = c * eta
    sigma = sigma0 * (1.0 + sigma_growth * R / (L + 1e-9))
    A = A_info0 / ((1.0 + R) ** alpha_decay)
    prof = A * ring_profile(r, R, sigma)
    Ex += prof * np.cos(th)
    Ey += prof * np.sin(th)
    tx, ty = tangential(th)
    Bx += prof * tx
    By += prof * ty
    return Ex, Ey, Bx, By


def info_reemit_fields(XX: np.ndarray, YY: np.ndarray, eta: float):
    if eta < eta_star:
        z = np.zeros_like(XX)
        return z, z, z, z
    Ex = np.zeros_like(XX)
    Ey = np.zeros_like(YY)
    Bx = np.zeros_like(XX)
    By = np.zeros_like(YY)
    r = np.hypot(XX, YY) + 1e-9
    th = np.arctan2(YY, XX)
    R = c * (eta - eta_star)
    sigma = sigma0 * (1.0 + sigma_growth * R / (L + 1e-9))
    A = A_reemit0 / ((1.0 + R) ** alpha_decay)
    prof = A * ring_profile(r, R, sigma)
    Ex += prof * np.cos(th)
    Ey += prof * np.sin(th)
    tx, ty = tangential(th)
    Bx += prof * tx
    By += prof * ty
    return Ex, Ey, Bx, By


def total_fields(XX: np.ndarray, YY: np.ndarray, eta: float):
    Emx, Emy, Bmx, Bmy = matter_fields(XX, YY, eta)
    Einx, Einy, Binx, Biny = info_incoming_fields(XX, YY, eta)
    Erox, Eroy, Brox, Broy = info_reemit_fields(XX, YY, eta)
    return Emx + Einx + Erox, Emy + Einy + Eroy, Bmx + Binx + Brox, Bmy + Biny + Broy


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    etas = np.linspace(0, eta_end, N_FRAMES)

    # fixed color scales
    maxE = 0.0
    maxB = 0.0
    for eta in etas:
        Ex, Ey, Bx, By = total_fields(X, Y, float(eta))
        maxE = max(maxE, float(np.hypot(Ex, Ey).max()))
        maxB = max(maxB, float(np.hypot(Bx, By).max()))

    vmaxE = maxE * 1.02
    vmaxB = maxB * 1.02

    with imageio.get_writer(
        out_gif, mode="I", duration=0.09, loop=0, palettesize=64, subrectangles=True
    ) as writer:
        for eta in etas:
            eta = float(eta)
            Ex, Ey, Bx, By = total_fields(X, Y, eta)
            magE = np.hypot(Ex, Ey)
            magB = np.hypot(Bx, By)
            Exs, Eys, Bxs, Bys = total_fields(Xs, Ys, eta)

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
            fig.colorbar(imE, cax=caxE).set_label("|E|")

            imB = axB.imshow(
                magB,
                extent=[-L, L, -L, L],
                origin="lower",
                vmin=0,
                vmax=vmaxB,
                cmap="viridis",
            )
            axB.streamplot(xs, ys, Bxs, Bys, color="cyan", density=0.55, linewidth=0.7)
            fig.colorbar(imB, cax=caxB).set_label("|B|")

            for ax in (axE, axB):
                ax.set_xlim(-L, L)
                ax.set_ylim(-L, L)
                ax.set_aspect("equal")
                ax.set_xlabel("x")
                ax.set_ylabel("y")
                ax.plot(0, 0, "wo", markersize=5)
                if eta < eta_star:
                    ax.plot(d, 0, marker="*", color="white", markersize=7)

            H_val = h0 if eta < eta_star else h0 + 1
            fig.suptitle(
                f"Conformal time η={eta:0.2f}   H(core)={H_val}   "
                f"(η*={eta_star:0.2f})   centers separated at η=0 by d={d}",
                color="white",
                y=0.98,
                fontsize=10,
            )

            canvas = FigureCanvas(fig)
            canvas.draw()
            img = np.frombuffer(canvas.tostring_rgb(), dtype=np.uint8)
            img = img.reshape(canvas.get_width_height()[::-1] + (3,))
            writer.append_data(img)
            plt.close(fig)

    print(f"Saved to {out_gif}")


if __name__ == "__main__":
    main()
