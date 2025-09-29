#!/usr/bin/env python3
from __future__ import annotations

"""RSD (fσ₈) 用の軽量尤度ラッパ雛形。

`data/rsd/rsd_points.yml` などに整理した観測値を読み込み、モデルから
計算された fσ₈(z) との一致度を χ² で評価する。モデル値は呼び出し側
で計算し、同じ順番で与えることを想定している。
"""

import json
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

import numpy as np

from analysis.lightweight_likelihood import (
    GaussianDataset,
    aggregate_results,
    evaluate_gaussian_likelihood,
    load_gaussian_datasets,
)
from src.cosmo.growth_solver import Cosmology, growth_factor

DEFAULT_PATH = Path('data/rsd/rsd_points.yml')
CFG_PATH = Path('cfg/early_fdb.json')


def _load_mu_config(path: Path = CFG_PATH) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {'eps_max': 0.1, 'a_on': 1/21, 'da': 0.02, 'k_c': 0.2}


def _growth_table(cfg: dict, *, use_mu_late: bool, k_eval: float = 0.05) -> dict:
    cos = Cosmology()
    a_grid = np.geomspace(1e-4, 1.0, 512)
    kwargs = {
        'eps_max': cfg.get('eps_max', 0.1),
        'a_on': cfg.get('a_on', 1/21),
        'da': cfg.get('da', 0.02),
        'k_c': cfg.get('k_c', 0.2),
        'k_sup': cfg.get('k_sup'),
        'n_sup': cfg.get('n_sup', 2.0),
    }
    D = growth_factor(a_grid, k_eval, cosmo=cos, use_mu_late=use_mu_late, **kwargs)
    ln_a = np.log(a_grid)
    ln_D = np.log(np.clip(D, 1e-12, None))
    dlnD_dlna = np.gradient(ln_D, ln_a)
    D_at_1 = float(D[-1]) if D[-1] != 0 else 1.0
    return {'ln_a': ln_a, 'ln_D': ln_D, 'dlnD_dlna': dlnD_dlna, 'D_at_1': D_at_1}


def predict_fsigma8(
    z: Sequence[float],
    *,
    cfg: Optional[dict] = None,
    use_mu_late: bool = True,
    sigma8_0: float = 0.811,
    k_eval: float = 0.05,
) -> np.ndarray:
    """Late‑FDB（もしくはΛCDM）から fσ₈(z) を推定する補助関数。"""

    cfg = cfg or _load_mu_config()
    table = _growth_table(cfg, use_mu_late=use_mu_late, k_eval=k_eval)
    ln_a = table['ln_a']
    ln_D = table['ln_D']
    dlnD = table['dlnD_dlna']
    D_at_1 = table['D_at_1']
    target_ln_a = np.log(1.0 / (1.0 + np.asarray(z, dtype=float)))
    ln_D_interp = np.interp(target_ln_a, ln_a, ln_D)
    dlnD_interp = np.interp(target_ln_a, ln_a, dlnD)
    D_ratio = np.exp(ln_D_interp) / D_at_1
    sigma8 = sigma8_0 * D_ratio
    return sigma8 * dlnD_interp


def load_rsd_datasets(path: Path = DEFAULT_PATH, *, select: Optional[List[str]] = None) -> List[GaussianDataset]:
    datasets = load_gaussian_datasets(path)
    if select:
        allow = set(select)
        datasets = [ds for ds in datasets if ds.short_name in allow or ds.name in allow]
    if not datasets:
        raise ValueError('No RSD datasets selected.')
    return datasets


def evaluate_rsd(model_values: Iterable[Iterable[float]], *,
                 path: Path = DEFAULT_PATH,
                 param_count: int = 0,
                 select: Optional[List[str]] = None) -> dict:
    """RSD 観測とモデル値を突き合わせて χ²/AICc を算出する。"""

    datasets = load_rsd_datasets(path, select=select)
    model_list = list(model_values)
    if len(model_list) != len(datasets):
        raise ValueError(f"model_values length {len(model_list)} does not match datasets {len(datasets)}")
    results = []
    for ds, vec in zip(datasets, model_list):
        vec_arr = np.array(list(vec), dtype=float)
        results.append(evaluate_gaussian_likelihood(ds, vec_arr, param_count=param_count))
    return aggregate_results(results, param_count=param_count)


def evaluate_rsd_from_growth(*,
                             path: Path = DEFAULT_PATH,
                             select: Optional[List[str]] = None,
                             use_mu_late: bool = True,
                             sigma8_0: float = 0.811,
                             k_eval: float = 0.05,
                             param_count: int = 0,
                             cfg: Optional[dict] = None) -> dict:
    """Late‑FDB / ΛCDM 成長率から自動的に fσ₈ を生成して評価する。"""

    datasets = load_rsd_datasets(path, select=select)
    cfg = cfg or _load_mu_config()
    results = []
    for ds in datasets:
        if ds.redshift is None:
            raise ValueError(f"dataset {ds.name} lacks redshift information")
        model_vec = predict_fsigma8(ds.redshift, cfg=cfg, use_mu_late=use_mu_late, sigma8_0=sigma8_0, k_eval=k_eval)
        results.append(evaluate_gaussian_likelihood(ds, model_vec, param_count=param_count))
    return aggregate_results(results, param_count=param_count)
