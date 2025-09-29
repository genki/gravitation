#!/usr/bin/env python3
"""Solar-system penalty helper for FDB/Late-FDB parameter sets."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Any

from src.cosmo.mu_late import mu_late

AU_METERS = 1.495978707e11
MPC_METERS = 3.085677581e22
G_SOLAR_AT_1AU_M_S2 = 5.931674617160913e-3  # GM_sun / r^2 at 1 AU
DEFAULT_A_MAX = 1.0e-13  # m s^-2


@dataclass(frozen=True)
class SolarPenaltyResult:
    mu_at_au: float
    delta_mu: float
    delta_a_m_s2: float
    delta_a_ratio: float
    a_max_m_s2: float
    k_au_1_per_mpc: float
    pass_bound: bool

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['status'] = 'pass' if self.pass_bound else 'fail'
        return d


def _au_to_k_mpc(radius_au: float) -> float:
    radius_m = float(radius_au) * AU_METERS
    radius_mpc = radius_m / MPC_METERS
    return 1.0 / max(radius_mpc, 1e-30)


def compute_solar_penalty(cfg: Dict[str, Any], *,
                          radius_au: float = 1.0,
                          a_max_m_s2: float = DEFAULT_A_MAX) -> SolarPenaltyResult:
    """Compute the Solar-system penalty for Late-FDB parameters.

    Parameters
    ----------
    cfg : dict
        Dictionary with keys {eps_max, a_on, da, k_c}. Missing keys fall back to defaults.
    radius_au : float
        Radius at which to evaluate the penalty (default: 1 AU).
    a_max_m_s2 : float
        Allowed excess acceleration (m s^-2) over GR at the chosen radius.
    """
    eps_max = float(cfg.get('eps_max', 0.0))
    a_on = float(cfg.get('a_on', 1.0 / 21.0))
    da = float(cfg.get('da', 0.02))
    k_c = float(cfg.get('k_c', 0.2))
    k = _au_to_k_mpc(radius_au)
    mu = float(
        mu_late(
            a=1.0,
            k=k,
            eps_max=eps_max,
            a_on=a_on,
            da=da,
            k_c=k_c,
            k_sup=cfg.get('k_sup'),
            n_sup=cfg.get('n_sup', 2.0),
        )
    )
    delta_mu = abs(mu - 1.0)
    delta_a = delta_mu * G_SOLAR_AT_1AU_M_S2
    ratio = delta_a / max(a_max_m_s2, 1e-30)
    pass_bound = delta_a <= a_max_m_s2 + 1e-18  # small tolerance
    return SolarPenaltyResult(
        mu_at_au=mu,
        delta_mu=delta_mu,
        delta_a_m_s2=delta_a,
        delta_a_ratio=ratio,
        a_max_m_s2=a_max_m_s2,
        k_au_1_per_mpc=k,
        pass_bound=pass_bound,
    )


__all__ = ['compute_solar_penalty', 'SolarPenaltyResult', 'DEFAULT_A_MAX']
