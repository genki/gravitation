#!/usr/bin/env python3
from __future__ import annotations
import yaml
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REL = ROOT / 'data' / 'weak_lensing' / 'kids450_release' / 'KiDS-450_COSMIC_SHEAR_DATA_RELEASE'


def load_vector(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    arr = np.loadtxt(path)
    if arr.ndim != 2 or arr.shape[1] < 3:
        raise RuntimeError(f'Unexpected vector format: {path}')
    return arr[:, 0], arr[:, 1], arr[:, 2]


def load_cov(path: Path) -> np.ndarray:
    cov = np.loadtxt(path)
    if cov.ndim != 2 or cov.shape[0] != cov.shape[1]:
        raise RuntimeError(f'Unexpected covariance shape: {cov.shape}')
    return cov


def main() -> int:
    vec_p = REL / 'DATA_VECTOR' / 'KiDS-450_xi_pm_tomographic_data_vector.dat'
    cov_p = REL / 'COV_MAT' / 'Cov_mat_all_scales.txt'
    if not vec_p.exists() or not cov_p.exists():
        print('missing vector or covariance files')
        return 2
    theta, xip, xim = load_vector(vec_p)
    cov: np.ndarray
    try:
        cov = load_cov(cov_p)
    except Exception:
        # Try COO-like analytic covariance (i, j, val)
        coo_p = REL / 'COV_MAT' / 'xipmcutcov_KiDS-450_analytic_inc_m.dat'
        coo = np.loadtxt(coo_p)
        if coo.ndim != 2 or coo.shape[1] != 3:
            raise
        i = coo[:, 0].astype(int)
        j = coo[:, 1].astype(int)
        v = coo[:, 2].astype(float)
        N = int(max(i.max(), j.max()))  # 1-based想定
        cov = np.zeros((N, N), dtype=float)
        for ii, jj, vv in zip(i, j, v):
            cov[ii-1, jj-1] = vv
            cov[jj-1, ii-1] = vv
    n = len(theta) * 2  # xi+ and xi- concatenated
    if cov.shape[0] != n:
        m = min(cov.shape[0], n)
        cov = cov[:m, :m]
        theta = theta[: m // 2]
        xip = xip[: m // 2]
        xim = xim[: m // 2]
    data = {
        'datasets': [
            {
                'name': 'KiDS-450 tomographic (concatenated)',
                'short_name': 'kids450_concat',
                'reference': 'Hildebrandt et al. 2017, MNRAS 465, 1454',
                'url': 'http://kids.strw.leidenuniv.nl/cs2016/',
                'enabled': False,
                'observables': [
                    {'name': 'xi_plus', 'units': 'dimensionless'},
                    {'name': 'xi_minus', 'units': 'dimensionless'},
                ],
                'theta_arcmin': [float(t) for t in theta],
                'data': [[float(a), float(b)] for a, b in zip(xip, xim)],
                'covariance': cov.tolist(),
                'notes': [
                    'Concatenated vector across tomographic pairs as distributed; covariance mapped accordingly.',
                    '正式評価では個別ビンへ分割し、対応する共分散ブロックを用いる。',
                ],
            }
        ]
    }
    out = ROOT / 'data' / 'weak_lensing' / 'kids450_xi_full_cov.yml'
    out.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
