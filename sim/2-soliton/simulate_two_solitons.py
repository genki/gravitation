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
out_gif = OUT_DIR / "two_soliton_V1_3d_z0_fixedsim_120f.gif"

# ==============================
# Time parameters (conformal time)
# ==============================
# Note: keep the time interval, reduce sampling density by 1/2.
N_FRAMES = 120
eta_star = 8.0  # resonance time
eta_end = 32.0  # includes re-emission phase
c = 1.0

# ==============================
# Spatial domain (V1 style) + 3D grid (z=0 slice visualized)
# ==============================
L = 10.0
nx_bg = 110  # background grid (x,y)
nz_bg = 41  # z grid (3D simulation backbone)
nx_sl = 24  # streamline grid (x,y)
nz_sl = 21  # z grid for streamline fields

x = np.linspace(-L, L, nx_bg)
y = np.linspace(-L, L, nx_bg)
z = np.linspace(-L, L, nz_bg)
X, Y = np.meshgrid(x, y)

xs = np.linspace(-L, L, nx_sl)
ys = np.linspace(-L, L, nx_sl)
zs = np.linspace(-L, L, nz_sl)
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

def _stack_z(XX: np.ndarray, YY: np.ndarray, zz: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # broadcast (ny,nx) with (nz,) -> (nz,ny,nx)
    nz = int(zz.shape[0])
    XX3 = np.broadcast_to(XX, (nz,) + XX.shape)
    YY3 = np.broadcast_to(YY, (nz,) + YY.shape)
    ZZ3 = np.broadcast_to(zz[:, None, None], (nz,) + XX.shape)
    return XX3, YY3, ZZ3


# ==============================
# Field definitions
# ==============================
def matter_fields_3d(XX: np.ndarray, YY: np.ndarray, zz: np.ndarray, eta: float):
    n = h0 if eta < eta_star else h0 + 1
    A = A_m_pre if eta < eta_star else A_m_post
    XX3, YY3, ZZ3 = _stack_z(XX, YY, zz)
    r = np.sqrt(XX3**2 + YY3**2 + ZZ3**2) + 1e-9
    th = np.arctan2(YY3, XX3)
    amp = A * np.exp(-((r / sigma_m) ** 2))
    angle = n * th
    tx, ty = tangential(angle)
    Ex = amp * tx
    Ey = amp * ty
    Ez = np.zeros_like(Ex)
    angleB = angle + np.pi / 2
    bx, by = tangential(angleB)
    Bx = 0.95 * amp * bx
    By = 0.95 * amp * by
    Bz = np.zeros_like(Bx)
    return Ex, Ey, Ez, Bx, By, Bz


def ring_profile(r: np.ndarray, R: float, sigma: float) -> np.ndarray:
    return np.exp(-((r - R) ** 2) / (2 * sigma**2))


def info_incoming_fields_3d(XX: np.ndarray, YY: np.ndarray, zz: np.ndarray, eta: float):
    XX3, YY3, ZZ3 = _stack_z(XX, YY, zz)
    Ex = np.zeros_like(XX3)
    Ey = np.zeros_like(YY3)
    Ez = np.zeros_like(ZZ3)
    Bx = np.zeros_like(XX3)
    By = np.zeros_like(YY3)
    Bz = np.zeros_like(ZZ3)
    cx, cy = info_center
    dx = XX3 - cx
    dy = YY3 - cy
    dz = ZZ3
    r = np.sqrt(dx**2 + dy**2 + dz**2) + 1e-9
    rt = np.hypot(dx, dy) + 1e-9
    R = c * eta
    sigma = sigma0 * (1.0 + sigma_growth * R / (L + 1e-9))
    A = A_info0 / ((1.0 + R) ** alpha_decay)
    prof = A * ring_profile(r, R, sigma)
    Ex += prof * (dx / r)
    Ey += prof * (dy / r)
    Ez += prof * (dz / r)
    # Choose a simple azimuthal B around z-axis (perpendicular to radial in xy).
    Bx += prof * (-dy / rt)
    By += prof * (dx / rt)
    return Ex, Ey, Ez, Bx, By, Bz


def info_reemit_fields_3d(XX: np.ndarray, YY: np.ndarray, zz: np.ndarray, eta: float):
    if eta < eta_star:
        XX3, YY3, ZZ3 = _stack_z(XX, YY, zz)
        z0 = np.zeros_like(XX3)
        return z0, z0, z0, z0, z0, z0
    XX3, YY3, ZZ3 = _stack_z(XX, YY, zz)
    Ex = np.zeros_like(XX3)
    Ey = np.zeros_like(YY3)
    Ez = np.zeros_like(ZZ3)
    Bx = np.zeros_like(XX3)
    By = np.zeros_like(YY3)
    Bz = np.zeros_like(ZZ3)
    dx = XX3
    dy = YY3
    dz = ZZ3
    r = np.sqrt(dx**2 + dy**2 + dz**2) + 1e-9
    rt = np.hypot(dx, dy) + 1e-9
    R = c * (eta - eta_star)
    sigma = sigma0 * (1.0 + sigma_growth * R / (L + 1e-9))
    A = A_reemit0 / ((1.0 + R) ** alpha_decay)
    prof = A * ring_profile(r, R, sigma)
    Ex += prof * (dx / r)
    Ey += prof * (dy / r)
    Ez += prof * (dz / r)
    Bx += prof * (-dy / rt)
    By += prof * (dx / rt)
    return Ex, Ey, Ez, Bx, By, Bz


def total_fields_3d(XX: np.ndarray, YY: np.ndarray, zz: np.ndarray, eta: float):
    Emx, Emy, Emz, Bmx, Bmy, Bmz = matter_fields_3d(XX, YY, zz, eta)
    Einx, Einy, Einz, Binx, Biny, Binz = info_incoming_fields_3d(XX, YY, zz, eta)
    Erox, Eroy, Eroz, Brox, Broy, Broz = info_reemit_fields_3d(XX, YY, zz, eta)
    return (
        Emx + Einx + Erox,
        Emy + Einy + Eroy,
        Emz + Einz + Eroz,
        Bmx + Binx + Brox,
        Bmy + Biny + Broy,
        Bmz + Binz + Broz,
    )


def _z0_index(zz: np.ndarray) -> int:
    return int(np.argmin(np.abs(zz - 0.0)))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    etas = np.linspace(0, eta_end, N_FRAMES)
    iz0_bg = _z0_index(z)
    iz0_sl = _z0_index(zs)

    # fixed color scales
    maxE = 0.0
    maxB = 0.0
    for eta in etas:
        Ex, Ey, Ez, Bx, By, Bz = total_fields_3d(X, Y, z, float(eta))
        Ex0, Ey0, Ez0 = Ex[iz0_bg], Ey[iz0_bg], Ez[iz0_bg]
        Bx0, By0, Bz0 = Bx[iz0_bg], By[iz0_bg], Bz[iz0_bg]
        maxE = max(maxE, float(np.sqrt(Ex0**2 + Ey0**2 + Ez0**2).max()))
        maxB = max(maxB, float(np.sqrt(Bx0**2 + By0**2 + Bz0**2).max()))

    vmaxE = maxE * 1.02
    vmaxB = maxB * 1.02

    with imageio.get_writer(
        out_gif, mode="I", duration=0.09, loop=0, palettesize=64, subrectangles=True
    ) as writer:
        for eta in etas:
            eta = float(eta)
            Ex, Ey, Ez, Bx, By, Bz = total_fields_3d(X, Y, z, eta)
            Ex0, Ey0, Ez0 = Ex[iz0_bg], Ey[iz0_bg], Ez[iz0_bg]
            Bx0, By0, Bz0 = Bx[iz0_bg], By[iz0_bg], Bz[iz0_bg]
            magE = np.sqrt(Ex0**2 + Ey0**2 + Ez0**2)
            magB = np.sqrt(Bx0**2 + By0**2 + Bz0**2)

            Exs, Eys, Ezs, Bxs, Bys, Bzs = total_fields_3d(Xs, Ys, zs, eta)
            Exs0, Eys0 = Exs[iz0_sl], Eys[iz0_sl]
            Bxs0, Bys0 = Bxs[iz0_sl], Bys[iz0_sl]

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
            axE.streamplot(xs, ys, Exs0, Eys0, color="red", density=0.55, linewidth=0.7)
            fig.colorbar(imE, cax=caxE).set_label("|E|")

            imB = axB.imshow(
                magB,
                extent=[-L, L, -L, L],
                origin="lower",
                vmin=0,
                vmax=vmaxB,
                cmap="viridis",
            )
            axB.streamplot(xs, ys, Bxs0, Bys0, color="cyan", density=0.55, linewidth=0.7)
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
                f"(η*={eta_star:0.2f})   z=0 slice   centers separated at η=0 by d={d}",
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
