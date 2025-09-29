from __future__ import annotations

import math
from typing import Callable, Tuple

import numpy as np


def ring_kernel_G_num(R: float, rho: float, eps: float, ntheta: int = 720) -> float:
    """Numerically integrate G(R,rho;eps) over theta.

    G(R, rho; eps) = \int_0^{2pi} (R - rho cosθ) / (R^2 + rho^2 - 2 R rho cosθ + eps^2) dθ
    """
    if R <= 0 and rho <= 0:
        return 0.0
    th = np.linspace(0.0, 2.0 * math.pi, int(max(ntheta, 180)), endpoint=False)
    num = (R - rho * np.cos(th))
    den = (R * R + rho * rho - 2.0 * R * rho * np.cos(th) + eps * eps)
    return float(np.trapz(num / den, th))


def disk_inv1_gr(
    R_vals: np.ndarray,
    Sigma_of_R: Callable[[np.ndarray], np.ndarray],
    eps: float = 0.3,
    n_rho: int = 256,
    ntheta: int = 720,
) -> np.ndarray:
    """Axisymmetric disk: compute g_R(R) from 1/r-term using ring integration.

    g_R(R) = - alpha_line * \int_0^∞ dρ ρ Σ(ρ) G(R,ρ;ε)
    Here alpha_line is factored out (user scales the result externally).
    """
    R_vals = np.asarray(R_vals, dtype=float)
    rmax = float(np.nanmax(R_vals))
    # integrate rho from 0..R_int_max (a bit beyond)
    rho_max = max(5.0 * rmax, rmax + 10.0 * eps)
    rho = np.linspace(0.0, rho_max, int(max(n_rho, 64)))
    Sigma = np.asarray(Sigma_of_R(rho), dtype=float)
    out = np.zeros_like(R_vals, dtype=float)
    for i, R in enumerate(R_vals):
        G = np.array([ring_kernel_G_num(R, r, eps, ntheta=ntheta) for r in rho])
        integrand = rho * Sigma * G
        out[i] = float(np.trapz(integrand, rho))
    return out


def rod_inv1_field_local(
    u: np.ndarray,
    v: np.ndarray,
    L: float,
    eps: float = 0.3,
    lam0: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Finite rod along u-axis from s∈[-L/2, L/2]; line density lam0.

    Returns unit-strength (alpha_line=1) field components (gu, gv) in the local rod frame.
    g(u,v) = - alpha_line * lam0 * ∫ ds (r - r_s) / (|r - r_s|^2 + eps^2)
    Closed forms:
      a = v^2 + eps^2, t = s-u
      ∫ (u-s)/( (u-s)^2 + a ) ds = 0.5 ln( (s-u)^2 + a ) with a minus sign by substitution
      ∫ v/( (u-s)^2 + a ) ds = (v/√a) arctan( (s-u)/√a )
    """
    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    a = v * v + eps * eps
    sqrt_a = np.sqrt(a)
    t2 = (L * 0.5) - u
    t1 = (-L * 0.5) - u
    # u-component integral (with sign)
    Iu = 0.5 * (np.log(t1 * t1 + a) - np.log(t2 * t2 + a))
    # v-component integral
    Iv = (v / (sqrt_a + 1e-12)) * (np.arctan(t2 / (sqrt_a + 1e-12)) - np.arctan(t1 / (sqrt_a + 1e-12)))
    gu = -lam0 * Iu
    gv = -lam0 * Iv
    return gu, gv


def rotate_field(gu: np.ndarray, gv: np.ndarray, angle_deg: float) -> Tuple[np.ndarray, np.ndarray]:
    th = math.radians(angle_deg)
    c, s = math.cos(th), math.sin(th)
    gx = gu * c - gv * s
    gy = gu * s + gv * c
    return gx, gy


def rod_inv1_field_xy(
    x: np.ndarray,
    y: np.ndarray,
    L: float,
    eps: float = 0.3,
    lam0: float = 1.0,
    angle_deg: float = 0.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Field of a finite rod of length L at angle_deg in the (x,y) plane.

    The rod is centered at the origin; rotate to local (u,v), integrate, rotate back.
    """
    th = math.radians(angle_deg)
    c, s = math.cos(th), math.sin(th)
    u = x * c + y * s
    v = -x * s + y * c
    gu, gv = rod_inv1_field_local(u, v, L=L, eps=eps, lam0=lam0)
    gx, gy = rotate_field(gu, gv, angle_deg)
    return gx, gy
