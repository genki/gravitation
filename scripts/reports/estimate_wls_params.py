#!/usr/bin/env python3
"""学習クラスタ（Abell1689・CL0024など）から WLS パラメタ (σ0, c, trim, N_eff) を推定するスクリプト。

- Σ_e を用いて σ^2 = σ0^2 + c·Σ_e のパラメタをグリッド探索で最適化
- ROI 外縁のフェザートリム (trim_frac, trim_iter) も同時に最適化
- AICc の N は自己相関を考慮した N_eff を用いる (N_eff = N / (1 + 2 Σ ρ_k))
- 推定結果を JSON で保存し、ホールドアウト評価で共通使用できるようにする

実行例:
    python scripts/reports/estimate_wls_params.py --out config/wls_params.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import fields
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

import numpy as np
from scipy import ndimage as ndi

try:
    from astropy.io import fits
except Exception as exc:  # pragma: no cover - fallback when astropy missing
    raise SystemExit(
        "astropy が必要です。pip install astropy で導入してください: %s" % exc
    )

from scripts.cluster.min_kernel import MinKernelParams, predict_kappa

# -----------------------------------------------------
# Utility functions (shared with make_bullet_holdout.py but kept local to avoid import cycles)
# -----------------------------------------------------

def _apply_edge_trim(mask: np.ndarray, frac: float = 0.05, iterations: int = 1) -> np.ndarray:
    """Apply uniform border trim + binary erosion to stabilise PSF/high-pass edge effects."""
    h, w = mask.shape
    trim = int(max(0, round(min(h, w) * frac)))
    if trim > 0:
        mask = mask.copy()
        mask[:trim, :] = False
        mask[-trim:, :] = False
        mask[:, :trim] = False
        mask[:, -trim:] = False
    if iterations > 0:
        mask = ndi.binary_erosion(mask, iterations=iterations, border_value=0)
    return mask


def _sigma_map_from_params(se_obs: np.ndarray, sigma0: float, coeff: float) -> np.ndarray:
    """Construct σ map = sqrt(σ0^2 + c·Σ_e) with clipping to avoid degeneracy."""
    se = np.clip(se_obs.astype(float), 0.0, None)
    sigma_sq = sigma0 ** 2 + coeff * se
    floor_sq = max((sigma0 * 0.1) ** 2, 1e-8)
    sigma_sq = np.maximum(sigma_sq, floor_sq)
    sigma = np.sqrt(sigma_sq)
    sigma[~np.isfinite(sigma)] = sigma0
    return sigma


def _autocorr_rhos(resid_norm: np.ndarray, mask: np.ndarray, max_lag: int = 8) -> List[float]:
    """Return list of average lag autocorrelations along x/y for lags = 1..max_lag."""
    arr = np.where(mask, resid_norm, np.nan)
    mu = np.nanmean(arr)
    arrc = arr - mu
    var = np.nanmean(arrc ** 2)
    if not np.isfinite(var) or var <= 0:
        return []
    rhos: List[float] = []
    for lag in range(1, max_lag + 1):
        vals: List[float] = []
        if arrc.shape[1] > lag:
            horiz_mask = mask[:, :-lag] & mask[:, lag:]
            if np.any(horiz_mask):
                prod = arrc[:, :-lag] * arrc[:, lag:]
                vals.append(np.nanmean(prod[horiz_mask]) / var)
        if arrc.shape[0] > lag:
            vert_mask = mask[:-lag, :] & mask[lag:, :]
            if np.any(vert_mask):
                prod = arrc[:-lag, :] * arrc[lag:, :]
                vals.append(np.nanmean(prod[vert_mask]) / var)
        if vals:
            rhos.append(float(np.nanmean(vals)))
    return [float(r) for r in rhos if np.isfinite(r)]


def _load_min_kernel_params(path: Path) -> MinKernelParams:
    data = json.loads(path.read_text())
    allowed = {f.name for f in fields(MinKernelParams)}
    kwargs = {k: v for k, v in data.items() if k in allowed}
    # Ensure tuples where expected
    if 'gate_sigmas' in kwargs:
        kwargs['gate_sigmas'] = tuple(kwargs['gate_sigmas'])
    return MinKernelParams(**kwargs)


def _load_cluster_maps(cluster_root: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Load omega_cut, sigma_e, kappa_obs and return along with pixel scale."""
    oc = cluster_root / 'omega_cut.fits'
    se = cluster_root / 'sigma_e.fits'
    ko = cluster_root / 'kappa_obs.fits'
    if not (oc.exists() and se.exists() and ko.exists()):
        raise FileNotFoundError(f"required FITS missing under {cluster_root}")
    omega = fits.getdata(oc).astype(float)
    sigma_e = fits.getdata(se).astype(float)
    kappa_obs = fits.getdata(ko).astype(float)
    hdr = fits.getheader(oc)
    pix = float(hdr.get('PIXKPC', 1.0))
    return omega, sigma_e, kappa_obs, pix


def _regrid_to(target_shape: Tuple[int, int], arr: np.ndarray) -> np.ndarray:
    if arr.shape == target_shape:
        return arr
    zoom_y = target_shape[0] / arr.shape[0]
    zoom_x = target_shape[1] / arr.shape[1]
    return ndi.zoom(arr, zoom=(zoom_y, zoom_x), order=1)


def evaluate_combo(
    cluster_data: Dict[str, Dict[str, np.ndarray]],
    sigma0: float,
    coeff: float,
    trim_frac: float,
    trim_iter: int,
    max_lag: int = 8,
) -> Tuple[float, Dict[str, dict]]:
    """Return mean AICc across clusters and per-cluster diagnostics."""
    k_align = 2  # Δx, Δy alignmentのみ
    per_cluster: Dict[str, dict] = {}
    scores: List[float] = []
    for name, payload in cluster_data.items():
        k_obs = payload['k_obs']
        k_pred = payload['k_pred']
        sigma_e = payload['sigma_e']
        mask = np.isfinite(k_obs) & np.isfinite(k_pred) & np.isfinite(sigma_e)
        mask = _apply_edge_trim(mask, frac=trim_frac, iterations=trim_iter)
        valid = int(mask.sum())
        if valid <= k_align + 2:
            continue
        sigma_map = _sigma_map_from_params(sigma_e, sigma0, coeff)
        resid = (k_obs - k_pred)
        resid_norm = np.where(mask, resid / sigma_map, 0.0)
        chi2 = float(np.nansum((resid[mask] / sigma_map[mask]) ** 2))
        rhos = _autocorr_rhos(resid_norm, mask, max_lag=max_lag)
        rho_pos = sum(r for r in rhos if r > 0)
        denom = 1.0 + 2.0 * rho_pos
        if not np.isfinite(denom) or denom <= 0:
            denom = 1.0
        N_eff = max(1, int(round(valid / denom)))
        block_pix = int(max(4, round(math.sqrt(valid / max(N_eff, 1)))))
        aicc = float(chi2 + 2 * k_align + (2 * k_align * (k_align + 1)) / max(N_eff - k_align - 1, 1))
        scores.append(aicc)
        per_cluster[name] = {
            'chi2': chi2,
            'N': valid,
            'N_eff': N_eff,
            'block_pix': block_pix,
            'rho_sum_pos': rho_pos,
            'rhos': rhos,
            'aicc': aicc,
        }
    if not scores:
        return float('inf'), per_cluster
    mean_score = float(np.mean(scores))
    return mean_score, per_cluster


def main() -> int:
    ap = argparse.ArgumentParser(description='WLS パラメタ推定')
    ap.add_argument('--train', type=str, default='', help='学習クラスタ（カンマ区切り)。未指定なら params_cluster.json の train_clusters を使用')
    ap.add_argument('--params', type=str, default='data/cluster/params_cluster.json', help='MinKernelParams を読む JSON パス')
    ap.add_argument('--out', type=str, default='config/wls_params.json', help='推定結果を書き出すパス')
    ap.add_argument('--sigma0', type=str, default='0.1:0.6:0.05', help='σ0 の探索範囲 (start:stop:step)')
    ap.add_argument('--coeff', type=str, default='0.0:0.6:0.05', help='c の探索範囲 (start:stop:step)')
    ap.add_argument('--trim-frac', type=str, default='0.05,0.07,0.09', help='trim_frac 候補')
    ap.add_argument('--trim-iter', type=str, default='1,2', help='trim_iter 候補')
    ap.add_argument('--max-lag', type=int, default=8, help='自己相関計算の最大ラグ')
    args = ap.parse_args()

    params_path = Path(args.params)
    if not params_path.exists():
        raise SystemExit(f'パラメタファイル {params_path} が見つかりません')
    min_params = _load_min_kernel_params(params_path)

    if args.train.strip():
        train_names = [s.strip() for s in args.train.split(',') if s.strip()]
    else:
        raw = json.loads(params_path.read_text())
        train_names = raw.get('train_clusters') or ['Abell1689', 'CL0024']

    cluster_data: Dict[str, Dict[str, np.ndarray]] = {}
    for name in train_names:
        root = Path('data/cluster') / name
        try:
            omega, sigma_e, k_obs, pix = _load_cluster_maps(root)
        except Exception as exc:
            print(f'[warn] {name}: {exc}')
            continue
        k_pred = predict_kappa(omega, sigma_e, pix, min_params)
        if k_pred.shape != k_obs.shape:
            k_pred = _regrid_to(k_obs.shape, k_pred)
        if sigma_e.shape != k_obs.shape:
            sigma_e = _regrid_to(k_obs.shape, sigma_e)
        cluster_data[name] = {
            'k_obs': k_obs.astype(float),
            'k_pred': k_pred.astype(float),
            'sigma_e': sigma_e.astype(float),
        }
    if not cluster_data:
        raise SystemExit('学習対象クラスタが読み込めませんでした')

    def parse_range(spec: str) -> List[float]:
        if ':' in spec:
            start, stop, step = [float(x) for x in spec.split(':')]
            vals = []
            v = start
            # inclusive stop with floating tolerance
            while v <= stop + 1e-9:
                vals.append(round(v, 10))
                v += step
            return vals
        return [float(x) for x in spec.split(',') if x.strip()]

    sigma0_candidates = parse_range(args.sigma0)
    coeff_candidates = parse_range(args.coeff)
    trim_frac_candidates = parse_range(args.trim_frac)
    trim_iter_candidates = [int(round(x)) for x in parse_range(args.trim_iter)]

    best = None
    diagnostics = None
    total_iters = len(sigma0_candidates) * len(coeff_candidates) * len(trim_frac_candidates) * len(trim_iter_candidates)
    iter_idx = 0
    for trim_frac in trim_frac_candidates:
        for trim_iter in trim_iter_candidates:
            for sigma0 in sigma0_candidates:
                for coeff in coeff_candidates:
                    iter_idx += 1
                    score, per_cluster = evaluate_combo(cluster_data, sigma0, coeff, trim_frac, trim_iter, max_lag=args.max_lag)
                    if best is None or score < best:
                        best = score
                        diagnostics = (sigma0, coeff, trim_frac, trim_iter, per_cluster)
                    if iter_idx % 50 == 0:
                        print(f'[progress] {iter_idx}/{total_iters} 探索中 (best AICc={best:.4f})')
    if diagnostics is None:
        raise SystemExit('適切なパラメタが見つかりませんでした')

    sigma0_best, coeff_best, trim_frac_best, trim_iter_best, per_cluster = diagnostics
    # 集計: block_pix はクラスタ中央値を採用
    block_pix_vals = [v['block_pix'] for v in per_cluster.values() if 'block_pix' in v]
    block_pix = int(round(float(np.median(block_pix_vals)))) if block_pix_vals else 27
    rho_sum_vals = [v.get('rho_sum_pos', 0.0) for v in per_cluster.values()]
    rho_sum_mean = float(np.mean(rho_sum_vals)) if rho_sum_vals else 0.0

    output = {
        'sigma0': float(sigma0_best),
        'c': float(coeff_best),
        'trim_frac': float(trim_frac_best),
        'trim_iter': int(trim_iter_best),
        'block_pix': int(block_pix),
        'rho_sum_pos_mean': rho_sum_mean,
        'max_lag': int(args.max_lag),
        'train_clusters': list(per_cluster.keys()),
        'per_cluster': per_cluster,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding='utf-8')
    print(f'[done] 保存しました: {out_path} (σ0={sigma0_best:.3f}, c={coeff_best:.3f}, trim_frac={trim_frac_best:.3f})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
