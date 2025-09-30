#!/usr/bin/env python3
from __future__ import annotations
import yaml
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REL = ROOT / 'data' / 'weak_lensing' / 'kids450_release' / 'KiDS-450_COSMIC_SHEAR_DATA_RELEASE'


def load_data_vector(path: Path):
    # Format per KiDS-450 release: columns [theta(arcmin), xi_plus(11,...), xi_minus(...)] stacked by tomo pairs
    arr = np.loadtxt(path)
    # The official vector is concatenated per pair; since schema differs across releases, we will emit a single YAML with full vector
    return arr


def save_yaml_full_vector(arr: np.ndarray, out: Path) -> None:
    thetas = arr[:, 0].tolist()
    xip = arr[:, 1].tolist()
    xim = arr[:, 2].tolist() if arr.shape[1] >= 3 else []
    data = {
        'datasets': [
            {
                'name': 'KiDS-450 tomographic full vector',
                'short_name': 'kids450_full',
                'reference': 'Hildebrandt et al. 2017, MNRAS 465, 1454',
                'url': 'http://kids.strw.leidenuniv.nl/cs2016/',
                'enabled': True,
                'observables': [
                    {'name': 'xi_plus', 'units': 'dimensionless'},
                    {'name': 'xi_minus', 'units': 'dimensionless'},
                ],
                'theta_arcmin': thetas,
                'data': [[float(a), float(b)] for a, b in zip(xip, (xim or [0.0]*len(xip)))],
                'notes': ['Vector concatenated across tomographic pairs as distributed (see release readme).'],
            }
        ]
    }
    out.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding='utf-8')


def main() -> int:
    dv = REL / 'DATA_VECTOR' / 'KiDS-450_xi_pm_tomographic_data_vector.dat'
    if not dv.exists():
        print('missing data vector at', dv)
        return 2
    arr = load_data_vector(dv)
    out = ROOT / 'data' / 'weak_lensing' / 'kids450_xi_full.yml'
    save_yaml_full_vector(arr, out)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

