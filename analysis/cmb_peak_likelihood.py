#!/usr/bin/env python3
from __future__ import annotations

"""CMB TT/TE/EE ピーク高さ・比を扱う軽量尤度ラッパ雛形。"""

from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np

from analysis.lightweight_likelihood import (
    GaussianDataset,
    aggregate_results,
    evaluate_gaussian_likelihood,
    load_gaussian_datasets,
)

DEFAULT_PATH = Path('data/cmb/peak_points.yml')


def load_cmb_peak_datasets(path: Path = DEFAULT_PATH, *, select: Optional[List[str]] = None) -> List[GaussianDataset]:
    datasets = load_gaussian_datasets(path)
    if select:
        allow = set(select)
        datasets = [ds for ds in datasets if ds.short_name in allow or ds.name in allow]
    if not datasets:
        raise ValueError('No CMB peak datasets selected.')
    return datasets


def evaluate_cmb_peaks(model_values: Iterable[Iterable[float]], *,
                        path: Path = DEFAULT_PATH,
                        param_count: int = 0,
                        select: Optional[List[str]] = None) -> dict:
    datasets = load_cmb_peak_datasets(path, select=select)
    model_list = list(model_values)
    if len(model_list) != len(datasets):
        raise ValueError(f"model_values length {len(model_list)} does not match datasets {len(datasets)}")
    results = []
    for ds, vec in zip(datasets, model_list):
        arr = np.array(list(vec), dtype=float)
        results.append(evaluate_gaussian_likelihood(ds, arr.reshape(-1), param_count=param_count))
    return aggregate_results(results, param_count=param_count)
