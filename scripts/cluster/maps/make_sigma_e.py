#!/usr/bin/env python3
from __future__ import annotations
import json
import numpy as np
from pathlib import Path


def main() -> int:
    manifest = Path('data/cluster/manifest.json')
    if not manifest.exists():
        print('error: missing manifest; run prep/reproject_all.py first')
        return 1
    info = json.loads(manifest.read_text(encoding='utf-8'))
    out_dir = Path('data/cluster/maps'); out_dir.mkdir(parents=True, exist_ok=True)
    # For each cluster entry we try to load pre-resampled maps (as .npy) if available; otherwise emit a stub.
    for key in ['bullet']:
        sigma_path = out_dir / f'{key}_sigma_e.npy'
        xray_npy = Path(f'data/cluster/{key}/xray.npy')
        temp_npy = Path(f'data/cluster/{key}/temp.npy')
        if xray_npy.exists():
            Ix = np.load(xray_npy)
            if temp_npy.exists():
                T = np.load(temp_npy)
                # crude cooling function proxy Λ(T) ~ T^{1/2}
                lam = np.sqrt(np.clip(T, 1e-3, None))
            else:
                lam = 1.0
            sigma_e = np.sqrt(np.clip(Ix, 0.0, None) / np.maximum(lam, 1e-6))
            np.save(sigma_path, sigma_e)
            print('wrote', sigma_path)
        else:
            # write an empty placeholder
            np.save(sigma_path, np.zeros((256, 256), dtype=float))
            print('stub (no data):', sigma_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

