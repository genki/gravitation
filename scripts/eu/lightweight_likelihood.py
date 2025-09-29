#!/usr/bin/env python3
"""Utility helpers for lightweight cosmological likelihoods.

This module provides small building blocks that will be reused when we wire in
RSD (fσ₈), weak lensing 2PCF, and CMB peak-height summary statistics.  The goal
is to keep the evaluation logic simple enough that it can run inside
`make repro`/CI without heavy external dependencies.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import yaml


@dataclass
class DataVector:
    """Container for a 1-D data vector with covariance."""

    z: np.ndarray
    values: np.ndarray
    covariance: np.ndarray

    def chi2(self, model: Sequence[float]) -> float:
        """Return χ² given a model evaluated at the same sampling points."""

        model_arr = np.asarray(model, dtype=float)
        if model_arr.shape != self.values.shape:
            raise ValueError("model array has incompatible shape")
        diff = self.values - model_arr
        cov_inv = np.linalg.inv(self.covariance)
        return float(diff.T @ cov_inv @ diff)

    def sigma_vector(self) -> np.ndarray:
        """Return 1σ uncertainties derived from the diagonal of the covariance."""

        return np.sqrt(np.diag(self.covariance))


def load_yaml_vector(path: Path) -> DataVector:
    """Load a lightweight likelihood vector stored as YAML."""

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    for key in ("z", "values", "covariance"):
        if key not in payload:
            raise ValueError(f"YAML file {path} missing key '{key}'")
    z = np.asarray(payload["z"], dtype=float)
    values = np.asarray(payload["values"], dtype=float)
    cov = np.asarray(payload["covariance"], dtype=float)
    if cov.shape != (values.size, values.size):
        raise ValueError("covariance must be square and match values length")
    return DataVector(z=z, values=values, covariance=cov)


def build_model_from_callable(z: Iterable[float], fn) -> np.ndarray:
    """Evaluate a simple callable on the supplied sampling points."""

    z_arr = np.asarray(list(z), dtype=float)
    return np.asarray([fn(val) for val in z_arr], dtype=float)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a lightweight χ²")
    parser.add_argument("data", type=Path, help="YAML file with z/values/covariance")
    parser.add_argument(
        "--model",
        choices=["constant"],
        default="constant",
        help="Toy model to evaluate (more options will be added for RSD/WL/CMB)",
    )
    parser.add_argument(
        "--amp",
        type=float,
        default=1.0,
        help="Amplitude for the toy constant model",
    )
    args = parser.parse_args()

    data_vec = load_yaml_vector(args.data)
    if args.model == "constant":
        model = np.full_like(data_vec.values, args.amp)
    else:
        raise ValueError(f"Unsupported model '{args.model}'")
    chi2 = data_vec.chi2(model)
    print(f"χ²={chi2:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
