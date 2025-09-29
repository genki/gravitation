#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from scripts.fdb.shared_params_loader import load as load_params


def main() -> int:
    sp = Path('data/shared_params.json')
    cv = Path('data/results/cv_shared_summary.json')
    out = {'ok': False, 'reason': '', 'shared': None, 'cv': None}
    try:
        params_v2 = load_params(sp)
        out['shared'] = {
            'epsilon': params_v2.theta_cos.epsilon,
            'k0': params_v2.theta_cos.k0,
            'm': params_v2.theta_cos.m,
            'gas_scale': params_v2.gas_scale if params_v2.gas_scale is not None else params_v2.theta_opt.omega0,
        }
    except Exception:
        out['reason'] = 'shared_params.json missing or invalid'
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 1
    try:
        c = json.loads(cv.read_text(encoding='utf-8'))
        out['cv'] = c
    except Exception:
        out['reason'] = 'cv_shared_summary.json missing or invalid'
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 1
    # Compare μ(k) and gas_scale
    try:
        smu = out['shared']
        sg = float(smu['gas_scale'])
        # pick adopted shared from CV (most frequent train_best)
        counts = {}
        for f in c.get('folds', []):
            b = f.get('train_best', {})
            t = (b.get('mu_eps'), b.get('mu_k0'), b.get('mu_m'))
            if None in t: continue
            counts[t] = counts.get(t, 0) + 1
        if counts:
            eps, k0, m = max(counts.items(), key=lambda it: it[1])[0]
        else:
            agg = c.get('aggregate', {})
            eps = agg.get('mu_eps')
            k0 = agg.get('mu_k0')
            m = agg.get('mu_m')
        cg = float(c.get('aggregate', {}).get('gas_scale', sg))
        ok = (
            abs(float(smu['epsilon']) - float(eps)) < 1e-6 and
            abs(float(smu['k0']) - float(k0)) < 1e-6 and
            int(round(float(smu['m']))) == int(round(float(m))) and
            abs(float(sg) - float(cg)) < 1e-6
        )
        out['ok'] = bool(ok)
        out['reason'] = '' if ok else 'mismatch between shared_params.json and CV summary'
    except Exception as e:
        out['reason'] = f'comparison error: {e}'
        out['ok'] = False
    print(json.dumps(out, indent=2, ensure_ascii=False))
    return 0 if out['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
