#!/usr/bin/env python3
from __future__ import annotations

"""複数天体の FDB 方向指標を一括計算するユーティリティ。"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import yaml

from scripts.galaxies.compute_fdb_signatures import compute_signatures, load_array


def _resolve_path(base: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = (base / path).resolve()
    return path


def run_batch(config_path: Path, *, dry_run: bool = False) -> Dict[str, Any]:
    payload = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    base = config_path.parent
    results = {}
    for entry in payload.get('targets', []):
        if entry.get('enabled', True) is False:
            continue
        name = entry['name']
        residual = load_array(_resolve_path(base, entry['residual']))
        sigma_e = load_array(_resolve_path(base, entry['sigma_e']))
        omega_cut = load_array(_resolve_path(base, entry['omega_cut']))
        pix_kpc = float(entry['pix_kpc'])
        bands = entry.get('bands', '4:8,8:16')
        rr_q = float(entry.get('rr_quantile', 0.85))
        result = compute_signatures(
            residual,
            sigma_e,
            omega_cut,
            pix_kpc=pix_kpc,
            bands=bands,
            rr_quantile=rr_q,
        )
        results[name] = result
        out_path = entry.get('out')
        if out_path and not dry_run:
            out_p = _resolve_path(base, out_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description='Batch compute FDB shadow signatures for multiple systems')
    ap.add_argument('config', help='YAML configuration with target entries')
    ap.add_argument('--dry-run', action='store_true', help='Compute in-memory only (no file writes)')
    ap.add_argument('--out', help='Optional aggregated JSON output path')
    args = ap.parse_args()

    config_path = Path(args.config)
    results = run_batch(config_path, dry_run=args.dry_run)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, indent=2), encoding='utf-8')
        print('wrote aggregated results to', out_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
