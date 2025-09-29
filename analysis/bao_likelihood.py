#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from math import inf
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import numpy as np
import yaml
from scipy.stats import chi2

try:
    from classy import Class  # type: ignore
except ImportError:  # pragma: no cover - graceful fallback when CLASS is unavailable
    Class = None  # type: ignore

C_KMS = 299_792.458


@dataclass(frozen=True)
class Observable:
    kind: str
    label: str
    units: str


@dataclass
class BAODataset:
    name: str
    short_name: str
    reference: str
    url: str
    z: np.ndarray
    observables: List[Observable]
    data: np.ndarray
    covariance: np.ndarray
    notes: List[str]

    @property
    def vector(self) -> np.ndarray:
        return self.data.reshape(-1)

    @property
    def n_points(self) -> int:
        return self.vector.size

    @property
    def cov_inv(self) -> np.ndarray:
        return np.linalg.inv(self.covariance)

    @property
    def std(self) -> np.ndarray:
        return np.sqrt(np.diag(self.covariance))


def load_bao_datasets(path: Path = Path('data/bao/bao_points.yml')) -> List[BAODataset]:
    if not path.exists():
        raise FileNotFoundError(f"BAO data file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding='utf-8'))
    datasets = []
    for entry in raw.get('datasets', []):
        obs_cfg = entry.get('observables', [])
        observables = [Observable(kind=o['kind'], label=o.get('label', o['kind']), units=o.get('units', ''))
                       for o in obs_cfg]
        data = np.array(entry['data'], dtype=float)
        cov = np.array(entry['covariance'], dtype=float)
        datasets.append(BAODataset(
            name=entry['name'],
            short_name=entry.get('short_name', entry['name'].lower().replace(' ', '_')),
            reference=entry.get('reference', ''),
            url=entry.get('url', ''),
            z=np.array(entry['z'], dtype=float),
            observables=observables,
            data=data,
            covariance=cov,
            notes=entry.get('notes', []),
        ))
    return datasets


def _model_vector_for_dataset(cosmo: Class, dataset: BAODataset) -> np.ndarray:
    if Class is None:
        raise RuntimeError('CLASS is not available; cannot compute BAO predictions.')
    rd = float(cosmo.rs_drag())
    model_values: List[float] = []
    for z in dataset.z:
        dm = float(cosmo.angular_distance(z) * (1.0 + z))
        hz = float(cosmo.Hubble(z) * C_KMS)  # km s^-1 Mpc^-1
        for obs in dataset.observables:
            kind = obs.kind
            if kind == 'D_M':
                model_values.append(dm)
            elif kind == 'DM_over_rd':
                model_values.append(dm / rd)
            elif kind == 'H_z':
                model_values.append(hz)
            elif kind == 'H_z_times_rd':
                model_values.append(hz * rd)
            elif kind == 'H_z_times_rd_over_c':
                model_values.append(hz * rd / C_KMS)
            else:
                raise ValueError(f"Unsupported observable kind: {kind}")
    return np.array(model_values, dtype=float)


def _hash_matrix(matrix: np.ndarray) -> str:
    payload = json.dumps(matrix.tolist(), sort_keys=True).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def evaluate_bao_likelihood(class_params: Dict[str, float], *,
                            bao_file: Path = Path('data/bao/bao_points.yml'),
                            dataset_filter: Optional[Iterable[str]] = None,
                            param_count: int = 0) -> Dict[str, object]:
    if Class is None:
        raise RuntimeError('CLASS is not available; install classy to evaluate BAO likelihoods.')

    datasets = load_bao_datasets(bao_file)
    if dataset_filter is not None:
        allowed = {name for name in dataset_filter}
        datasets = [ds for ds in datasets if ds.short_name in allowed or ds.name in allowed]

    if not datasets:
        raise ValueError('No BAO datasets selected for evaluation.')

    cosmo = Class()
    cosmo.set(class_params)
    cosmo.compute()

    results = []
    chi2_total = 0.0
    ndof_total = 0
    for dataset in datasets:
        model_vec = _model_vector_for_dataset(cosmo, dataset)
        obs_vec = dataset.vector
        delta = obs_vec - model_vec
        chi2_val = float(delta.T @ dataset.cov_inv @ delta)
        ndof = dataset.n_points - param_count
        ndof = max(ndof, 1)
        chi2_total += chi2_val
        ndof_total += ndof
        std = dataset.std
        pulls = np.divide(delta, std, out=np.full_like(delta, np.nan), where=std > 0)
        per_point = []
        obs_per = dataset.data
        model_per = model_vec.reshape(obs_per.shape)
        for i, z in enumerate(dataset.z):
            for j, obs in enumerate(dataset.observables):
                idx = i * len(dataset.observables) + j
                per_point.append({
                    'z': float(z),
                    'observable': obs.kind,
                    'label': obs.label,
                    'units': obs.units,
                    'observed': float(obs_per[i, j]),
                    'model': float(model_per[i, j]),
                    'residual': float(delta[idx]),
                    'sigma': float(std[idx]),
                    'pull': float(pulls[idx]),
                })
        aicc = chi2_val if param_count == 0 else chi2_val + 2 * param_count + (
            2 * param_count * (param_count + 1) / max(dataset.n_points - param_count - 1, 1)
        )
        result = {
            'name': dataset.name,
            'short_name': dataset.short_name,
            'reference': dataset.reference,
            'url': dataset.url,
            'z': dataset.z.tolist(),
            'observables': [obs.kind for obs in dataset.observables],
            'chi2': chi2_val,
            'ndof': ndof,
            'aicc': aicc,
            'p_value': float(chi2.sf(chi2_val, ndof)),
            'observed': obs_per.tolist(),
            'model': model_per.tolist(),
            'per_point': per_point,
            'covariance_sha256': _hash_matrix(dataset.covariance),
            'notes': dataset.notes,
        }
        results.append(result)

    cosmo.struct_cleanup()
    cosmo.empty()

    total = {
        'chi2_total': chi2_total,
        'ndof_total': ndof_total,
        'aicc_total': chi2_total if param_count == 0 else chi2_total + 2 * param_count,
        'p_value_total': float(chi2.sf(chi2_total, ndof_total)),
        'datasets': results,
        'param_count': param_count,
        'bao_file': str(bao_file),
    }
    return total


__all__ = ['BAODataset', 'Observable', 'load_bao_datasets', 'evaluate_bao_likelihood']


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Evaluate BAO likelihood for CLASS parameters.')
    parser.add_argument('--bao-file', default='data/bao/bao_points.yml', help='Path to BAO data YAML file')
    parser.add_argument('--select', nargs='*', help='Dataset short_name(s) to include')
    parser.add_argument('--param-count', type=int, default=0, help='Effective parameter count for AICc')
    parser.add_argument('--class-params', default=None,
                        help='Path to JSON file with CLASS parameters (defaults to script baseline).')
    args = parser.parse_args()

    class_params = {
        'output': 'mPk',
        'P_k_max_1/Mpc': 2.0,
        'z_max_pk': 1.1,
        'Omega_b': 0.049,
        'Omega_cdm': 0.266,
        'h': 0.674,
        'A_s': 2.1e-9,
        'n_s': 0.965,
        'tau_reio': 0.0544,
    }
    if args.class_params:
        with open(args.class_params, 'r', encoding='utf-8') as fh:
            class_params.update(json.load(fh))

    result = evaluate_bao_likelihood(class_params,
                                     bao_file=Path(args.bao_file),
                                     dataset_filter=args.select,
                                     param_count=args.param_count)
    print(json.dumps(result, indent=2, ensure_ascii=False))
