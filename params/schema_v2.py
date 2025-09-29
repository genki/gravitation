#!/usr/bin/env python3
"""Light-weight schema helpers for shared FDB parameter set (v2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


class _ValidationError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise _ValidationError(message)


@dataclass(frozen=True)
class ThetaOpt:
    tau0: float
    omega0: float
    p: float

    def __post_init__(self) -> None:
        _require(self.tau0 >= 0.0, 'tau0 must be ≥ 0')
        _require(0.0 <= self.omega0 <= 1.0, 'omega0 must be in [0,1]')
        _require(0.5 <= self.p <= 2.5, 'p must be within [0.5, 2.5]')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThetaOpt":
        return cls(
            tau0=float(data['tau0']),
            omega0=float(data['omega0']),
            p=float(data['p']),
        )


@dataclass(frozen=True)
class ThetaIf:
    eta: float
    s_gate: float
    q_knee: float

    def __post_init__(self) -> None:
        _require(self.eta >= 0.0, 'eta must be ≥ 0')
        _require(self.s_gate >= 0.0, 's_gate must be ≥ 0')
        _require(0.0 <= self.q_knee <= 1.0, 'q_knee must be in [0,1]')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThetaIf":
        return cls(
            eta=float(data['eta']),
            s_gate=float(data['s_gate']),
            q_knee=float(data['q_knee']),
        )


@dataclass(frozen=True)
class ThetaAniso:
    g: float

    def __post_init__(self) -> None:
        _require(0.0 <= self.g <= 1.0, 'g must be in [0,1]')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThetaAniso":
        return cls(g=float(data['g']))


@dataclass(frozen=True)
class ThetaCos:
    epsilon: float
    s: float
    k0: float
    q: float
    m: float
    k_c: float
    n: float

    def __post_init__(self) -> None:
        _require(self.n >= 0.0, 'n must be ≥ 0')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ThetaCos":
        return cls(
            epsilon=float(data['epsilon']),
            s=float(data['s']),
            k0=float(data['k0']),
            q=float(data['q']),
            m=float(data['m']),
            k_c=float(data['k_c']),
            n=float(data['n']),
        )


@dataclass(frozen=True)
class FDBParameterSetV2:
    theta_opt: ThetaOpt
    theta_if: ThetaIf
    theta_aniso: ThetaAniso
    theta_cos: ThetaCos
    gas_scale: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FDBParameterSetV2":
        try:
            opt = ThetaOpt.from_dict(data['theta_opt'])
            gate = ThetaIf.from_dict(data['theta_if'])
            aniso = ThetaAniso.from_dict(data['theta_aniso'])
            cos = ThetaCos.from_dict(data['theta_cos'])
        except KeyError as exc:
            raise _ValidationError(f'missing key: {exc.args[0]}') from exc
        gas_scale = data.get('gas_scale')
        if gas_scale is not None:
            gas_scale = float(gas_scale)
        return cls(opt, gate, aniso, cos, gas_scale)


__all__ = [
    'FDBParameterSetV2',
    'ThetaOpt',
    'ThetaIf',
    'ThetaAniso',
    'ThetaCos',
]
