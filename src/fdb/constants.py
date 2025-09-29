"""Physical constants and derived factors.

SI units by default.
"""
from __future__ import annotations

G: float = 6.67430e-11        # m^3 kg^-1 s^-2
c: float = 2.99792458e8       # m s^-1
C: float = G / c              # appears in Λ = (G/c) ∫ ...
KAPPA: float = 1.0            # placeholder for κ = m c^2 bookkeeping (dimensionful outside scope)

