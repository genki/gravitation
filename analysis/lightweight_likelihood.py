#!/usr/bin/env python3
from __future__ import annotations

"""汎用的なガウス尤度ラッパの共通部品。

本モジュールは「観測データ→ベクトル化→χ²/AICc」を行う軽量尤度の
一貫したインターフェイスを提供する。RSD や弱レンズ 2PCF、CMB ピーク
比など共通の構造を持つ指標に対し、観測値とモデル値を突き合わせる
ための基盤として利用する。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np
import yaml
from scipy.stats import chi2


@dataclass
class GaussianObservable:
    """観測量のメタデータ。"""

    name: str
    units: str = ""
    label: Optional[str] = None


@dataclass
class GaussianDataset:
    """一次情報（観測値と共分散）を保持するコンテナ。"""

    name: str
    short_name: str
    reference: str
    url: str
    redshift: Optional[Sequence[float]]
    observables: List[GaussianObservable]
    data: np.ndarray
    covariance: np.ndarray
    notes: List[str]

    def vector(self) -> np.ndarray:
        return self.data.reshape(-1)

    def cov_inv(self) -> np.ndarray:
        return np.linalg.inv(self.covariance)

    def std(self) -> np.ndarray:
        return np.sqrt(np.diag(self.covariance))

    @property
    def n_points(self) -> int:
        return self.vector().size


def load_gaussian_datasets(path: Path | str, *, key: str = "datasets") -> List[GaussianDataset]:
    """YAML からガウス型観測データ群を読み込む。"""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"likelihood data file not found: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    datasets: List[GaussianDataset] = []
    for entry in payload.get(key, []):
        if entry.get('enabled', True) is False:
            continue
        observables = [
            GaussianObservable(
                name=obs.get("name", obs.get("kind", "")),
                units=obs.get("units", ""),
                label=obs.get("label"),
            )
            for obs in entry.get("observables", [])
        ]
        data = np.array(entry["data"], dtype=float)
        covariance = np.array(entry["covariance"], dtype=float)
        datasets.append(
            GaussianDataset(
                name=entry["name"],
                short_name=entry.get("short_name", entry["name"].lower().replace(" ", "_")),
                reference=entry.get("reference", ""),
                url=entry.get("url", ""),
                redshift=entry.get("z"),
                observables=observables,
                data=data,
                covariance=covariance,
                notes=entry.get("notes", []),
            )
        )
    return datasets


def evaluate_gaussian_likelihood(
    dataset: GaussianDataset,
    model_vector: Iterable[float],
    *,
    param_count: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """観測ベクトルとモデルベクトルから χ² / AICc を算出する。"""

    observed = dataset.vector()
    model = np.array(list(model_vector), dtype=float)
    if model.size != observed.size:
        raise ValueError(
            f"model vector length mismatch: expected {observed.size}, got {model.size}"
        )
    delta = observed - model
    cov_inv = dataset.cov_inv()
    chi2_val = float(delta.T @ cov_inv @ delta)
    ndof = max(dataset.n_points - param_count, 1)
    aicc = chi2_val if param_count == 0 else chi2_val + 2 * param_count + (
        2 * param_count * (param_count + 1) / max(dataset.n_points - param_count - 1, 1)
    )
    std = dataset.std()
    pulls = np.divide(delta, std, out=np.full_like(delta, np.nan), where=std > 0)
    result: Dict[str, Any] = {
        "name": dataset.name,
        "short_name": dataset.short_name,
        "reference": dataset.reference,
        "url": dataset.url,
        "chi2": chi2_val,
        "ndof": ndof,
        "aicc": aicc,
        "p_value": float(chi2.sf(chi2_val, ndof)),
        "observed": observed.tolist(),
        "model": model.tolist(),
        "residual": delta.tolist(),
        "pull": pulls.tolist(),
        "notes": dataset.notes,
    }
    if dataset.redshift is not None:
        result["z"] = list(map(float, dataset.redshift))
    if metadata:
        result["meta"] = metadata
    return result


def aggregate_results(results: Iterable[Dict[str, Any]], *, param_count: int = 0) -> Dict[str, Any]:
    """複数 dataset の結果を合算し、全体の χ²/AICc を返す。"""

    chi2_total = 0.0
    ndof_total = 0
    collected: List[Dict[str, Any]] = []
    for res in results:
        chi2_total += float(res["chi2"])
        ndof_total += int(res["ndof"])
        collected.append(res)
    return {
        "chi2_total": chi2_total,
        "ndof_total": ndof_total,
        "aicc_total": chi2_total if param_count == 0 else chi2_total + 2 * param_count,
        "p_value_total": float(chi2.sf(chi2_total, ndof_total)),
        "datasets": collected,
        "param_count": param_count,
    }
