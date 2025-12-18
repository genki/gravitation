from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HopfionSpec:
    p: int = 1
    q: int = 1
    kind: str = "retarded"  # "retarded" | "advanced"
    center: tuple[float, float, float] = (0.0, 0.0, 0.0)
    time_shift: float = 0.0  # evaluate at (eta - time_shift)
    # Rotation from base hopfion coordinates to lab coordinates.
    # Base hopfion uses the standard Bateman/Riemann–Silberstein construction.
    # We evaluate in base coords x',y',z' and map lab->base via R^T.
    rot: np.ndarray | None = None  # shape (3,3) or None for identity


def _as_rotation(rot: np.ndarray | None) -> np.ndarray:
    if rot is None:
        return np.eye(3)
    rot = np.asarray(rot, dtype=float)
    if rot.shape != (3, 3):
        raise ValueError("rot must be shape (3,3)")
    return rot


def _lab_to_base(
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    spec: HopfionSpec,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cx, cy, cz = spec.center
    xl = x - cx
    yl = y - cy
    zl = z - cz
    R = _as_rotation(spec.rot)
    # base = R^T * lab
    xb = R[0, 0] * xl + R[1, 0] * yl + R[2, 0] * zl
    yb = R[0, 1] * xl + R[1, 1] * yl + R[2, 1] * zl
    zb = R[0, 2] * xl + R[1, 2] * yl + R[2, 2] * zl
    return xb, yb, zb


def _bateman_alpha_beta(
    t: float, x: np.ndarray, y: np.ndarray, z: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Kedia et al. (2013) / Bateman construction choice:
    # alpha = (r^2 - t^2 - 1 + 2 i z) / (r^2 - (t - i)^2)
    # beta  = 2 (x - i y) / (r^2 - (t - i)^2)
    #
    # We also return D = r^2 - (t - i)^2 for reuse.
    r2 = x * x + y * y + z * z
    # D = r^2 - (t - i)^2 = (r^2 - t^2 + 1) + 2 i t
    D = (r2 - t * t + 1.0) + (2.0j * t)
    N_alpha = (r2 - t * t - 1.0) + (2.0j * z)
    N_beta = 2.0 * (x - 1.0j * y)
    alpha = N_alpha / D
    beta = N_beta / D
    return alpha, beta, D


def _grad_alpha_beta(
    t: float, x: np.ndarray, y: np.ndarray, z: np.ndarray
) -> tuple[tuple[np.ndarray, np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray, np.ndarray], np.ndarray, np.ndarray]:
    # Return (grad alpha), (grad beta), alpha, beta in base coordinates.
    alpha, beta, D = _bateman_alpha_beta(t, x, y, z)
    r2 = x * x + y * y + z * z
    N_alpha = (r2 - t * t - 1.0) + (2.0j * z)
    N_beta = 2.0 * (x - 1.0j * y)

    D2 = D * D

    # Derivatives
    dD_dx = 2.0 * x
    dD_dy = 2.0 * y
    dD_dz = 2.0 * z

    dNa_dx = 2.0 * x
    dNa_dy = 2.0 * y
    dNa_dz = (2.0 * z) + (2.0j)

    dNb_dx = 2.0 + 0.0j
    dNb_dy = -2.0j
    dNb_dz = 0.0 + 0.0j

    dalpha_dx = (dNa_dx * D - N_alpha * dD_dx) / D2
    dalpha_dy = (dNa_dy * D - N_alpha * dD_dy) / D2
    dalpha_dz = (dNa_dz * D - N_alpha * dD_dz) / D2

    dbeta_dx = (dNb_dx * D - N_beta * dD_dx) / D2
    dbeta_dy = (dNb_dy * D - N_beta * dD_dy) / D2
    dbeta_dz = (dNb_dz * D - N_beta * dD_dz) / D2

    grad_alpha = (dalpha_dx, dalpha_dy, dalpha_dz)
    grad_beta = (dbeta_dx, dbeta_dy, dbeta_dz)
    return grad_alpha, grad_beta, alpha, beta


def hopfion_fields(
    eta: float,
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
    spec: HopfionSpec,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return E,B for a Bateman-constructed null field.

    Uses F = E + i B = ∇(alpha^p) × ∇(beta^q).
    """
    # Map lab -> base coordinates.
    xb, yb, zb = _lab_to_base(x, y, z, spec)

    t = float(eta - spec.time_shift)

    # Base (retarded-like) field:
    grad_alpha, grad_beta, alpha, beta = _grad_alpha_beta(t, xb, yb, zb)

    p = int(spec.p)
    q = int(spec.q)
    if p < 1 or q < 1:
        raise ValueError("p,q must be positive integers")

    # grad(alpha^p) = p * alpha^(p-1) * grad(alpha)
    alpha_p_1 = alpha ** (p - 1) if p > 1 else 1.0 + 0.0j
    beta_q_1 = beta ** (q - 1) if q > 1 else 1.0 + 0.0j

    ax, ay, az = grad_alpha
    bx, by, bz = grad_beta

    g1x = (p * alpha_p_1) * ax
    g1y = (p * alpha_p_1) * ay
    g1z = (p * alpha_p_1) * az

    g2x = (q * beta_q_1) * bx
    g2y = (q * beta_q_1) * by
    g2z = (q * beta_q_1) * bz

    # Cross product g1 × g2 (complex)
    Fx = g1y * g2z - g1z * g2y
    Fy = g1z * g2x - g1x * g2z
    Fz = g1x * g2y - g1y * g2x

    # Advanced is time-reversal: F_adv(eta) = conj(F_base(-eta))
    if spec.kind == "advanced":
        grad_alpha_m, grad_beta_m, alpha_m, beta_m = _grad_alpha_beta(-t, xb, yb, zb)
        axm, aym, azm = grad_alpha_m
        bxm, bym, bzm = grad_beta_m
        alpha_p_1m = alpha_m ** (p - 1) if p > 1 else 1.0 + 0.0j
        beta_q_1m = beta_m ** (q - 1) if q > 1 else 1.0 + 0.0j
        g1xm = (p * alpha_p_1m) * axm
        g1ym = (p * alpha_p_1m) * aym
        g1zm = (p * alpha_p_1m) * azm
        g2xm = (q * beta_q_1m) * bxm
        g2ym = (q * beta_q_1m) * bym
        g2zm = (q * beta_q_1m) * bzm
        Fx = np.conjugate(g1ym * g2zm - g1zm * g2ym)
        Fy = np.conjugate(g1zm * g2xm - g1xm * g2zm)
        Fz = np.conjugate(g1xm * g2ym - g1ym * g2xm)
    elif spec.kind != "retarded":
        raise ValueError("spec.kind must be 'retarded' or 'advanced'")

    # Convert back to lab orientation: F_lab = R * F_base
    R = _as_rotation(spec.rot)
    Fx_lab = R[0, 0] * Fx + R[0, 1] * Fy + R[0, 2] * Fz
    Fy_lab = R[1, 0] * Fx + R[1, 1] * Fy + R[1, 2] * Fz
    Fz_lab = R[2, 0] * Fx + R[2, 1] * Fy + R[2, 2] * Fz

    Ex = np.real(Fx_lab)
    Ey = np.real(Fy_lab)
    Ez = np.real(Fz_lab)
    Bx = np.imag(Fx_lab)
    By = np.imag(Fy_lab)
    Bz = np.imag(Fz_lab)
    return Ex, Ey, Ez, Bx, By, Bz


def rotation_propagate_z_to_minus_x() -> np.ndarray:
    """Rotation matrix R such that base +z maps to lab -x."""
    return np.array(
        [
            [0.0, 0.0, -1.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
        ],
        dtype=float,
    )

