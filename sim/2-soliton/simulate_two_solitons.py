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
out_gif = OUT_DIR / "two_soliton_V1_hopfion_z0_shrinkphys_120f.gif"

# ==============================
# Time parameters (conformal time)
# ==============================
N_FRAMES = 120
eta_end = 32.0
c = 1.0

# ==============================
# Shrinking-universe coordinate mapping (visualization only)
# ==============================
# We keep *conformal fields* (E,B in conformal coordinates) but optionally
# visualize them on a fixed *physical* window via:
#   x_comoving = x_phys / a(eta)
# so that a null propagation radius ~ c*eta in comoving coordinates becomes
# ~ a(eta)*c*eta in physical coordinates, which can look "staying" when
# a(eta) ~ eta0/(eta+eta0).
USE_PHYSICAL_WINDOW = True
ETA0 = 8.0  # a(eta) = eta0/(eta+eta0), so a(eta)*eta -> eta0 as eta->inf


def scale_factor_a(eta: float) -> float:
    eta = float(eta)
    return float(ETA0 / (ETA0 + max(eta, 0.0)))


# ==============================
# Spatial domain (V1 style)
# ==============================
L = 10.0  # window half-size (interpreted as physical if USE_PHYSICAL_WINDOW=True)
nx_bg = 110  # background grid (x,y)
nx_sl = 24  # streamline grid

_xw = np.linspace(-L, L, nx_bg)
_yw = np.linspace(-L, L, nx_bg)
Xw, Yw = np.meshgrid(_xw, _yw)
Zw0 = np.zeros_like(Xw)

_xs = np.linspace(-L, L, nx_sl)
_ys = np.linspace(-L, L, nx_sl)
Xsw, Ysw = np.meshgrid(_xs, _ys)
Zsw0 = np.zeros_like(Xsw)

# ==============================
# Two-soliton configuration
# ==============================
d = 8.0  # initial separation along +x for the incoming info soliton
eta_star = d / c  # nominal "encounter time" marker (for annotation only)

# Diagnostics (why "advanced looks diffusive" etc.)
PRINT_DIAGNOSTICS = True
DIAG_GRID_L = 6.0
DIAG_GRID_N = 33

# For the advanced core: if time_shift=0, η increases will show the advanced pulse
# moving *away* from the convergence region in this particular Bateman solution,
# which can look like “diffusion” on a fixed z=0 slice. To visualize an *incoming*
# advanced pulse (approaching the core as η increases), shift its time origin so
# that the pulse arrives near η=eta_end.
MATTER_TIME_SHIFT = eta_end

MATTER = HopfionSpec(
    p=1,
    q=3,
    kind="advanced",
    center=(0.0, 0.0, 0.0),
    time_shift=MATTER_TIME_SHIFT,
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


def _coords_for_eta(eta: float, X: np.ndarray, Y: np.ndarray, Z: np.ndarray):
    if not USE_PHYSICAL_WINDOW:
        return X, Y, Z, 1.0
    a = scale_factor_a(eta)
    # Map from fixed physical window (Xw,Yw) to comoving coordinates.
    return X / a, Y / a, Z / a, a


def total_fields_conformal_z0(eta: float):
    Xc, Yc, Zc, _a = _coords_for_eta(eta, Xw, Yw, Zw0)
    Em = hopfion_fields(eta, Xc, Yc, Zc, MATTER)
    Ei = hopfion_fields(eta, Xc, Yc, Zc, INFO)
    Ex = Em[0] + Ei[0]
    Ey = Em[1] + Ei[1]
    Ez = Em[2] + Ei[2]
    Bx = Em[3] + Ei[3]
    By = Em[4] + Ei[4]
    Bz = Em[5] + Ei[5]
    return Ex, Ey, Ez, Bx, By, Bz


def total_fields_stream_z0(eta: float):
    Xc, Yc, Zc, _a = _coords_for_eta(eta, Xsw, Ysw, Zsw0)
    Em = hopfion_fields(eta, Xc, Yc, Zc, MATTER)
    Ei = hopfion_fields(eta, Xc, Yc, Zc, INFO)
    Ex = Em[0] + Ei[0]
    Ey = Em[1] + Ei[1]
    Bx = Em[3] + Ei[3]
    By = Em[4] + Ei[4]
    return Ex, Ey, Bx, By


def _diagnose_component(name: str, spec: HopfionSpec, eta: float) -> None:
    L = float(DIAG_GRID_L)
    n = int(DIAG_GRID_N)
    x = np.linspace(-L, L, n)
    X3, Y3, Z3 = np.meshgrid(x, x, x, indexing="ij")
    Ex, Ey, Ez, Bx, By, Bz = hopfion_fields(float(eta), X3, Y3, Z3, spec)
    u = 0.5 * (Ex * Ex + Ey * Ey + Ez * Ez + Bx * Bx + By * By + Bz * Bz)
    Sx = Ey * Bz - Ez * By
    Sy = Ez * Bx - Ex * Bz
    Sz = Ex * By - Ey * Bx
    dV = (2.0 * L / (n - 1)) ** 3
    Ut = float(u.sum() * dV)
    if not np.isfinite(Ut) or Ut <= 0:
        print(f"[diag] {name} eta={eta:.2f}: Ut invalid ({Ut})")
        return
    xbar = float((u * X3).sum() * dV / Ut)
    ybar = float((u * Y3).sum() * dV / Ut)
    zbar = float((u * Z3).sum() * dV / Ut)
    # Energy-weighted mean Poynting direction indicator.
    Smean_z = float(((Sz * u).sum() * dV / Ut))
    print(
        f"[diag] {name} eta={eta:.2f}: "
        f"centroid=({xbar:+.2f},{ybar:+.2f},{zbar:+.2f})  "
        f"<Sz>_u={Smean_z:+.3f}  time_shift={spec.time_shift:+.2f} kind={spec.kind}"
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    etas = np.linspace(0.0, eta_end, N_FRAMES)

    if PRINT_DIAGNOSTICS:
        # Diagnose each component propagation on a coarse 3D box.
        _diagnose_component("MATTER", MATTER, float(etas[0]))
        _diagnose_component("MATTER", MATTER, float(etas[len(etas) // 2]))
        _diagnose_component("MATTER", MATTER, float(etas[-1]))
        _diagnose_component("INFO", INFO, float(etas[0]))
        _diagnose_component("INFO", INFO, float(etas[len(etas) // 2]))
        _diagnose_component("INFO", INFO, float(etas[-1]))

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

            fig = plt.figure(figsize=(10.6, 4.2), dpi=240, facecolor="black")
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
            axE.streamplot(_xs, _ys, Exs, Eys, color="red", density=0.55, linewidth=0.7)
            fig.colorbar(imE, cax=caxE).set_label("|E| (conformal)")

            imB = axB.imshow(
                magB,
                extent=[-L, L, -L, L],
                origin="lower",
                vmin=0,
                vmax=vmaxB,
                cmap="viridis",
            )
            axB.streamplot(_xs, _ys, Bxs, Bys, color="cyan", density=0.55, linewidth=0.7)
            fig.colorbar(imB, cax=caxB).set_label("|B| (conformal)")

            for ax in (axE, axB):
                ax.set_xlim(-L, L)
                ax.set_ylim(-L, L)
                ax.set_aspect("equal")
                ax.set_xlabel("x (physical)" if USE_PHYSICAL_WINDOW else "x (comoving)")
                ax.set_ylabel("y (physical)" if USE_PHYSICAL_WINDOW else "y (comoving)")
                ax.plot(0, 0, "wo", markersize=5, label="matter center")
                ax.plot(d, 0, marker="*", color="white", markersize=7, label="info start")

            a = scale_factor_a(eta) if USE_PHYSICAL_WINDOW else 1.0
            fig.suptitle(
                "Two Bateman null fields (conformal Maxwell), z=0 slice  "
                f"η={eta:0.2f}  (η★≈{eta_star:0.2f})  a(η)={a:0.3f}  "
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
