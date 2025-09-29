#!/usr/bin/env python3
from __future__ import annotations
import json, hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from scripts.fdb.shared_params_loader import load as load_params


def sha12(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    except Exception:
        return ""


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    out_dir = root / 'paper'
    out_dir.mkdir(parents=True, exist_ok=True)
    vars_yml = out_dir / '_variables.yml'

    # Shared params
    params = load_params(root / 'data/shared_params.json')
    eps = params.theta_cos.epsilon
    k0 = params.theta_cos.k0
    m = params.theta_cos.m
    gas = params.gas_scale if params.gas_scale is not None else params.theta_opt.omega0

    # CV aggregate improvements
    cv = json.loads((root / 'data/results/cv_shared_summary.json').read_text(encoding='utf-8'))
    agg = cv.get('aggregate', {})
    delta_aicc = float(agg.get('delta_AICc', agg.get('delta_AIC', 0.0)))
    Ntot = int((agg.get('N_sum') or {}).get('ULW') or 0)
    Kgr = int((agg.get('K_sum') or {}).get('GR') or 0)
    Kulw = int((agg.get('K_sum') or {}).get('ULW') or 0)

    # Fingerprints to record reproducibility
    fp = {
        'shared_params_json': sha12(root / 'data/shared_params.json'),
        'cv_shared_summary_json': sha12(root / 'data/results/cv_shared_summary.json'),
    }

    # Emit Quarto/Pandoc variables YAML
    yml = []
    yml.append('title: "Apparent Gravitation from FDB of ULW-EM"')
    yml.append('subtitle: "Fair Tests on NGC 3198/2403 and Cross-Validation"')
    yml.append('params:')
    yml.append(f"  mu_eps: {eps}")
    yml.append(f"  mu_k0: {k0}")
    yml.append(f"  mu_m: {m}")
    yml.append(f"  gas_scale: {gas}")
    yml.append(f"  delta_aicc: {delta_aicc:.1f}")
    yml.append(f"  N_total: {Ntot}")
    yml.append(f"  k_sum_gr: {Kgr}")
    yml.append(f"  k_sum_ulw: {Kulw}")
    yml.append('fingerprints:')
    for k, v in fp.items():
        yml.append(f"  {k}: {v}")
    # Optional: bullet cluster metrics
    try:
        bmet = json.loads((Path('server/public/reports/cluster')/'bullet_metrics.json').read_text(encoding='utf-8'))
        yml.append('bullet:')
        yml.append(f"  offset_model_xray_kpc: {bmet.get('offset_model_xray_kpc')}")
        yml.append(f"  offset_model_gal_kpc: {bmet.get('offset_model_gal_kpc')}")
        yml.append(f"  scale_kpc_per_pix: {bmet.get('scale_kpc_per_pix')}")
    except Exception:
        pass
    vars_yml.write_text('\n'.join(yml) + '\n', encoding='utf-8')
    print('wrote', vars_yml)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
