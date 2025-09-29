from __future__ import annotations
"""
Toy model: random spherical thin shells acting as ULM-P surface sources.

Provides a numerical check that a single thin spherical shell produces
~1/r^2 field outside and ~0 inside (Gauss/shell theorem), when evaluated
via discrete surface sampling and Newtonian Green's function.
"""

import numpy as np


def sample_sphere_points(n: int, radius: float, rng: np.random.Generator | None = None) -> np.ndarray:
    rng = rng or np.random.default_rng()
    u = rng.uniform(0.0, 1.0, size=n)
    v = rng.uniform(0.0, 1.0, size=n)
    theta = 2 * np.pi * u
    phi = np.arccos(2 * v - 1)
    x = radius * np.sin(phi) * np.cos(theta)
    y = radius * np.sin(phi) * np.sin(theta)
    z = radius * np.cos(phi)
    return np.stack([x, y, z], axis=-1)


def accel_from_shell(
    r_eval: np.ndarray,
    R_shell: float,
    n_pts: int = 4096,
    mass_eff: float = 1.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Compute radial acceleration magnitude from a thin spherical shell.

    Parameters
    - r_eval: radii at which to evaluate |a(r)| (array-like, >0)
    - R_shell: shell radius
    - n_pts: number of surface samples for Monte Carlo integration
    - mass_eff: effective mass for normalization (G set to 1)

    Returns
    - |a(r)| for each r in r_eval
    """
    rng = rng or np.random.default_rng(42)
    points = sample_sphere_points(n_pts, R_shell, rng=rng)  # (n,3)
    # Uniform surface density over the shell: each point mass = M / n_pts
    m_pt = float(mass_eff) / float(n_pts)
    r_eval = np.asarray(r_eval, dtype=float)
    acc = np.zeros_like(r_eval)
    for i, r in enumerate(r_eval):
        # evaluate at (r,0,0) without loss of generality (spherical symmetry)
        x = np.array([r, 0.0, 0.0])
        d = x[None, :] - points  # (n,3)
        dist = np.linalg.norm(d, axis=1)
        # Avoid evaluating at the shell exactly
        dist = np.where(dist < 1e-9, 1e-9, dist)
        # Newtonian G=1 acceleration contributions: a = m/|r-r'|^2 in radial direction
        # Project onto radial unit vector (x/|x|) to get radial component
        e_r = x / (np.linalg.norm(x) + 1e-12)
        a_vec = (m_pt / (dist ** 3))[:, None] * d  # (n,3)
        a_r = np.dot(a_vec, e_r)
        acc[i] = np.sum(a_r)
    # Direction is inward (negative), return magnitude
    return np.abs(acc)


