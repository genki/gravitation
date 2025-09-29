#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import numpy as np
from astropy.io import fits

from analysis.shadow_bandpass import (
    BandSpec,
    ShadowBandpassEvaluator,
    build_rr_band_cache,
    build_se_band_info,
)
from scipy.ndimage import zoom


def compute_signatures(
    residual: np.ndarray,
    sigma_e: np.ndarray,
    omega_cut: np.ndarray,
    *,
    pix_kpc: float,
    bands: str = "4:8,8:16",
    rr_quantile: float = 0.85,
    block_size: int = 28,
) -> dict:
    if residual.shape != sigma_e.shape:
        scale_y = sigma_e.shape[0] / residual.shape[0]
        scale_x = sigma_e.shape[1] / residual.shape[1]
        residual = zoom(residual, (scale_y, scale_x), order=1)
    if omega_cut.shape != sigma_e.shape:
        scale_y = sigma_e.shape[0] / omega_cut.shape[0]
        scale_x = sigma_e.shape[1] / omega_cut.shape[1]
        omega_cut = zoom(omega_cut, (scale_y, scale_x), order=1)

    band_specs: List[BandSpec] = []
    for token in bands.split(','):
        token = token.strip()
        if not token:
            continue
        lam_min, lam_max = token.split(':')
        band_specs.append(BandSpec(name=f"band_{lam_min}_{lam_max}", lambda_min=float(lam_min), lambda_max=float(lam_max)))
    if not band_specs:
        raise ValueError("At least one band must be specified")

    se_info = build_se_band_info(sigma_e, band_specs)
    rr_cache = build_rr_band_cache(residual, band_specs)
    mask = np.isfinite(residual) & np.isfinite(sigma_e)
    evaluator = ShadowBandpassEvaluator(se_info, mask.astype(bool), block_size=block_size, rr_quantile=rr_quantile)
    result = evaluator.evaluate(rr_cache, mask)
    if result is None:
        raise RuntimeError("Failed to compute signatures (mask empty)")

    return {
        "S": result["S"],
        "Q2": result["Q2"],
        "rayleigh": result["rayleigh"],
        "v_test": result["v_test"],
        "band_details": result["band_details"],
        "n_dir": result["n_dir"],
        "rr_quantile": rr_quantile,
        "bands": bands,
        "pix_kpc": pix_kpc,
    }


def load_array(path: Path) -> np.ndarray:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() in {".fits", ".fit", ".fts"}:
        with fits.open(path) as hdul:
            arr = hdul[0].data.astype(float)
    elif path.suffix.lower() == ".npy":
        arr = np.load(path).astype(float)
    else:
        raise ValueError(f"Unsupported file type for {path}")
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array for {path}, got shape {arr.shape}")
    return arr


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute shadow/Q2 signatures for a galaxy residual map")
    ap.add_argument("--residual", required=True, help="Path to residual map (κ_obs−κ_model)")
    ap.add_argument("--sigma-e", required=True, help="Path to Σ_e map")
    ap.add_argument("--omega-cut", required=True, help="Path to ω_cut map")
    ap.add_argument("--pix-kpc", type=float, required=True, help="Pixel size in kpc")
    ap.add_argument("--out", required=True, help="Output JSON path")
    ap.add_argument("--rr-quantile", type=float, default=0.85, help="Quantile threshold for |∇R| (default 0.85)")
    ap.add_argument(
        "--bands",
        default="4:8,8:16",
        help="Comma-separated band definitions in pix (e.g. 4:8,8:16)",
    )
    args = ap.parse_args()

    residual = load_array(Path(args.residual))
    sigma_e = load_array(Path(args.sigma_e))
    omega_cut = load_array(Path(args.omega_cut))

    payload = compute_signatures(
        residual,
        sigma_e,
        omega_cut,
        pix_kpc=args.pix_kpc,
        bands=args.bands,
        rr_quantile=args.rr_quantile,
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
