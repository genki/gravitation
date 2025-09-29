#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from params.schema_v2 import FDBParameterSetV2, ThetaAniso, ThetaCos, ThetaIf, ThetaOpt
from scripts.migrate_params_v1_to_v2 import migrate_v1_to_v2


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


@dataclass(frozen=True)
class ParameterSet:
    theta_opt: ThetaOpt
    theta_if: ThetaIf
    theta_aniso: ThetaAniso
    theta_cos: ThetaCos
    gas_scale: float | None = None


SIGMA_REF = 1.0


def load(path: Path = Path('data/shared_params.json')) -> ParameterSet:
    payload = _read_json(path)
    if 'theta_opt' not in payload:
        payload = migrate_v1_to_v2(payload)
    params = FDBParameterSetV2.from_dict(payload)
    return ParameterSet(
        theta_opt=params.theta_opt,
        theta_if=params.theta_if,
        theta_aniso=params.theta_aniso,
        theta_cos=params.theta_cos,
        gas_scale=params.gas_scale,
    )


def to_legacy_dict(ps: ParameterSet) -> Dict[str, float]:
    tau0 = ps.theta_opt.tau0
    alpha = tau0 / SIGMA_REF if SIGMA_REF else tau0
    omega0 = ps.theta_opt.omega0
    legacy_xi = omega0 / max(1.0 - omega0, 1e-9) if omega0 < 1.0 else float('inf')
    g = ps.theta_aniso.g
    legacy_beta = g / max(1.0 - g, 1e-9) if g < 1.0 else float('inf')
    legacy = {
        'alpha': alpha,
        'xi': legacy_xi,
        'p': ps.theta_opt.p,
        'tau_q': 0.75,  # placeholder until physical derivation is wired everywhere
        'delta_tau_frac': ps.theta_if.eta,  # approximate inverse mapping; refined later
        's_gate': ps.theta_if.s_gate,
        'q_knee': ps.theta_if.q_knee,
        'beta': legacy_beta,
        'epsilon': ps.theta_cos.epsilon,
        's': ps.theta_cos.s,
        'k0': ps.theta_cos.k0,
        'q': ps.theta_cos.q,
        'm': ps.theta_cos.m,
        'k_c': ps.theta_cos.k_c,
        'n': ps.theta_cos.n,
    }
    if ps.gas_scale is not None:
        legacy['gas_scale'] = ps.gas_scale
    return legacy
