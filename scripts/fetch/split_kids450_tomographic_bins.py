#!/usr/bin/env python3
from __future__ import annotations
import yaml
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REL = ROOT / 'data' / 'weak_lensing' / 'kids450_release' / 'KiDS-450_COSMIC_SHEAR_DATA_RELEASE'


def load_vector(path: Path) -> np.ndarray:
    arr = np.loadtxt(path)
    if arr.ndim != 2 or arr.shape[1] < 3:
        raise RuntimeError(f'Unexpected format: {path} (shape={arr.shape})')
    return arr


def split_segments(arr: np.ndarray) -> list[tuple[np.ndarray, np.ndarray, np.ndarray]]:
    th = arr[:, 0]
    xp = arr[:, 1]
    xm = arr[:, 2]
    idx = [0]
    for i in range(1, len(th)):
        if th[i] < th[i - 1]:  # theta reset → new segment
            idx.append(i)
    idx.append(len(th))
    segs: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    for a, b in zip(idx[:-1], idx[1:]):
        segs.append((th[a:b], xp[a:b], xm[a:b]))
    return segs


def save_yaml(seg_id: int, theta: np.ndarray, xip: np.ndarray, xim: np.ndarray, out_dir: Path) -> Path:
    data = {
        'datasets': [
            {
                'name': f'KiDS-450 tomo segment {seg_id}',
                'short_name': f'kids450_seg{seg_id}',
                'reference': 'Hildebrandt et al. 2017, MNRAS 465, 1454',
                'url': 'http://kids.strw.leidenuniv.nl/cs2016/',
                'enabled': False,
                'observables': [
                    {'name': 'xi_plus', 'units': 'dimensionless'},
                    {'name': 'xi_minus', 'units': 'dimensionless'},
                ],
                'theta_arcmin': [float(t) for t in theta],
                'data': [[float(a), float(b)] for a, b in zip(xip, xim)],
                'notes': [
                    'Segmented from DATA_VECTOR; segment index is a placeholder for tomo bin pair.',
                    '共分散は未設定（後続でCOV_MATから対応付けます）。',
                ],
            }
        ]
    }
    out = out_dir / f'kids450_xi_tomo_seg{seg_id:02d}.yml'
    out.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding='utf-8')
    return out


def main() -> int:
    dv = REL / 'DATA_VECTOR' / 'KiDS-450_xi_pm_tomographic_data_vector.dat'
    if not dv.exists():
        print('missing', dv)
        return 2
    arr = load_vector(dv)
    segs = split_segments(arr)
    out_dir = ROOT / 'data' / 'weak_lensing'
    paths: list[str] = []
    for i, (th, xp, xm) in enumerate(segs, 1):
        out = save_yaml(i, th, xp, xm, out_dir)
        paths.append(str(out.relative_to(ROOT)))
    (out_dir / 'kids450_segments.json').write_text(yaml.safe_dump({'files': paths}, sort_keys=False, allow_unicode=True), encoding='utf-8')
    print('wrote', len(paths), 'segment YAMLs')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

