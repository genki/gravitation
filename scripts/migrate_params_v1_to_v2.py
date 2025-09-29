#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any, Dict

# Representative physical constants (placeholders, refine later)
SIGMA_REF = 1.0  # Msun pc^-2 equivalent surface density used for tau0 conversion
DEBYE_LENGTH_DEFAULT = 5.0  # kpc, fallback if missing (placeholder)
INTERFACE_WIDTH_DEFAULT = 5.0  # kpc

CLUSTER_PARAMS_PATH = Path('data/cluster/params_cluster.json')


def _load_cluster_defaults(path: Path = CLUSTER_PARAMS_PATH) -> Dict[str, Any]:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def load_v1(path: Path) -> dict:
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, dict):
        return data
    raise ValueError('shared_params v1 must be a JSON object')


def _pick(source: Dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        if key in source and source[key] is not None:
            try:
                return float(source[key])
            except Exception:
                continue
    return float(default)


def migrate_v1_to_v2(v1: dict) -> dict:
    cluster_defaults = _load_cluster_defaults()

    # Optical sector
    alpha = _pick(v1, 'alpha', default=_pick(cluster_defaults, 'alpha', default=0.6))
    xi = _pick(v1, 'xi', default=_pick(cluster_defaults, 'xi', default=0.0))
    p = _pick(v1, 'p', default=_pick(cluster_defaults, 'p', default=1.0))
    tau0 = alpha * SIGMA_REF
    # Map ξ∈[0,∞) to bounded albedo ω0∈[0,1)
    omega0 = xi / (1.0 + abs(xi)) if xi >= 0 else 0.0
    theta_opt = {"tau0": tau0, "omega0": omega0, "p": p}

    # Interface
    tau_q = _pick(v1, 'tau_q', default=_pick(cluster_defaults, 'tau_q', default=0.75))
    delta_tau_frac = _pick(v1, 'delta_tau_frac', default=_pick(cluster_defaults, 'delta_tau_frac', default=0.15))
    s_gate = _pick(v1, 's_gate', default=_pick(cluster_defaults, 's_gate', default=24.0))
    q_knee = _pick(v1, 'q_knee', default=_pick(cluster_defaults, 'q_knee', default=0.9))
    L_if = _pick(v1, 'interface_width_kpc', default=_pick(cluster_defaults, 'interface_width_kpc', default=INTERFACE_WIDTH_DEFAULT))
    lambda_D = _pick(v1, 'debye_length_kpc', default=_pick(cluster_defaults, 'debye_length_kpc', default=DEBYE_LENGTH_DEFAULT))
    eta = delta_tau_frac * L_if / max(lambda_D, 1e-6)
    theta_if = {"eta": eta, "s_gate": s_gate, "q_knee": q_knee}

    # Anisotropy
    beta = _pick(v1, 'beta', default=_pick(cluster_defaults, 'beta', default=0.8))
    g = beta / (1.0 + abs(beta)) if beta >= 0 else 0.0
    theta_aniso = {"g": g}

    # Cosmology / growth parameters
    mu_k = v1.get('mu_k', {}) if isinstance(v1.get('mu_k'), dict) else {}
    theta_cos = {
        "epsilon": _pick(mu_k, 'epsilon', 'eps', default=_pick(v1, 'epsilon', default=1.0)),
        "s": _pick(v1, 's', default=3.0),
        "k0": _pick(mu_k, 'k0', default=_pick(v1, 'k0', default=0.2)),
        "q": _pick(v1, 'q', default=1.0),
        "m": _pick(mu_k, 'm', default=_pick(v1, 'm', default=2.0)),
        "k_c": _pick(v1, 'k_c', default=0.3),
        "n": _pick(v1, 'n', default=2.0),
    }

    gas_scale = v1.get('gas_scale')
    if gas_scale is not None:
        try:
            gas_scale = float(gas_scale)
        except Exception:
            gas_scale = None

    return {
        "theta_opt": theta_opt,
        "theta_if": theta_if,
        "theta_aniso": theta_aniso,
        "theta_cos": theta_cos,
        "gas_scale": gas_scale,
        "mu_k": {
            "epsilon": theta_cos["epsilon"],
            "k0": theta_cos["k0"],
            "m": theta_cos["m"],
        },
        "tau0": theta_opt["tau0"],
        "omega0": theta_opt["omega0"],
        "eta": theta_if["eta"],
        "g": theta_aniso["g"],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description='Migrate shared_params v1 → v2')
    ap.add_argument('input', type=Path, help='shared_params.json (v1)')
    ap.add_argument('-o', '--output', type=Path, default=Path('data/shared_params_v2.json'))
    args = ap.parse_args()

    v1 = load_v1(args.input)
    v2 = migrate_v1_to_v2(v1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(v2, indent=2, ensure_ascii=False), encoding='utf-8')
    print('wrote', args.output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
