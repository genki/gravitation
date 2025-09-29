#!/usr/bin/env python3
"""Validate Bullet holdout summary against a reference baseline."""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

DEFAULT_CURRENT = Path('server/public/reports/cluster/Bullet_holdout.json')
DEFAULT_BASELINE = Path('data/baselines/bullet_holdout_reference.json')
DEFAULT_LOG = Path('logs/bullet_holdout_validation.log')


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"JSON not found: {path}")
    with path.open(encoding='utf-8') as f:
        return json.load(f)


def extract_metrics(data: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    delta = data.get('delta', {})
    out['delta_rot'] = float(delta.get('FDB_minus_rot', math.nan))
    out['delta_shift'] = float(delta.get('FDB_minus_shift', math.nan))
    rchi2 = data.get('rchi2', {})
    out['rchi2_fdb'] = float(rchi2.get('FDB', math.nan))
    ind = data.get('indicators') or {}
    s_shadow = ind.get('S_shadow')
    if not isinstance(s_shadow, dict):
        s_shadow = data.get('shadow', {}) if isinstance(data.get('shadow'), dict) else {}
    values = s_shadow.get('values', {}) if isinstance(s_shadow, dict) else {}
    out['S_shadow_global'] = float(values.get('global', math.nan))
    perm = s_shadow.get('perm', {}) if isinstance(s_shadow, dict) else {}
    out['p_perm'] = float(perm.get('p_perm_one_sided_pos', math.nan))
    out['p_fdr'] = float(perm.get('p_fdr', math.nan))
    # capture cos alignment for sanity
    if 'shear_phase_cos' in ind:
        out['shear_phase_cos'] = float(ind.get('shear_phase_cos'))
    return out


def compare(current: Dict[str, float], baseline: Dict[str, float], tolerances: Dict[str, float]) -> Tuple[bool, List[str]]:
    failures: List[str] = []
    for key, tol in tolerances.items():
        cur = current.get(key, math.nan)
        ref = baseline.get(key, math.nan)
        if math.isnan(cur) or math.isnan(ref):
            failures.append(f"{key}: missing (current={cur}, baseline={ref})")
            continue
        if abs(cur - ref) > tol:
            failures.append(f"{key}: |{cur} - {ref}| > {tol}")
    return (len(failures) == 0), failures


def append_log(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')
    with log_path.open('a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Bullet holdout summary vs reference")
    parser.add_argument('--current', type=Path, default=DEFAULT_CURRENT, help='Current Bullet_holdout.json path')
    parser.add_argument('--baseline', type=Path, default=DEFAULT_BASELINE, help='Reference baseline JSON path')
    parser.add_argument('--log', type=Path, default=DEFAULT_LOG, help='Validation log output path')
    args = parser.parse_args()

    current_data = load_json(args.current)
    baseline_data = load_json(args.baseline)

    current_metrics = extract_metrics(current_data)
    baseline_metrics = extract_metrics(baseline_data)

    tolerances = {
        'delta_rot': 1e-3,
        'delta_shift': 1e-3,
        'S_shadow_global': 1e-3,
        'p_perm': 1e-4,
        'p_fdr': 1e-4,
        'rchi2_fdb': 1e-3,
    }

    ok, failures = compare(current_metrics, baseline_metrics, tolerances)
    details = ", ".join(f"{k}={current_metrics.get(k)}" for k in sorted(current_metrics))
    if ok:
        append_log(args.log, f"PASS :: {details}")
        return 0
    append_log(args.log, f"FAIL :: {'; '.join(failures)} :: {details}")
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
