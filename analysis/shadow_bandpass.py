from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, MutableMapping, Optional

import numpy as np
from scipy import ndimage as ndi

__all__ = [
    "BandSpec",
    "scharr_axis",
    "ring_bandpass",
    "ring_bandpass_lambda",
    "morph_clean",
    "make_block_ids",
    "build_se_band_info",
    "build_rr_band_cache",
    "benjamini_hochberg",
    "ShadowBandpassEvaluator",
]


@dataclass(frozen=True)
class BandSpec:
    """Specification of a band-pass filter in real-space wavelength units."""

    name: str
    lambda_min: float
    lambda_max: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("band name must be non-empty")
        lam_min = float(self.lambda_min)
        lam_max = float(self.lambda_max)
        if not math.isfinite(lam_min) or not math.isfinite(lam_max):
            raise ValueError("lambda limits must be finite numbers")
        if lam_min <= 0 or lam_max <= 0:
            raise ValueError("lambda limits must be positive")
        if lam_max <= lam_min:
            raise ValueError("lambda_max must be greater than lambda_min")


def scharr_axis(arr: np.ndarray, axis: int) -> np.ndarray:
    """2-D Scharr derivative along the requested axis (0 = Y, 1 = X)."""

    if axis not in (0, 1):
        raise ValueError("axis must be 0 (y) or 1 (x)")
    kx = np.array([[3, 0, -3], [10, 0, -10], [3, 0, -3]], dtype=float) / 16.0
    ky = kx.T
    kernel = ky if axis == 0 else kx
    return ndi.convolve(arr, kernel, mode="reflect")


def ring_bandpass(arr: np.ndarray, k_low: float, k_high: float) -> np.ndarray:
    """Apply a ring-shaped band-pass filter in Fourier space."""

    if k_low <= 0 or k_high <= 0:
        raise ValueError("k_low/k_high must be positive")
    if k_high <= k_low:
        raise ValueError("k_high must be greater than k_low")
    arr_filled = np.nan_to_num(arr, nan=0.0)
    fy = np.fft.fftfreq(arr.shape[0]) * 2.0 * math.pi
    fx = np.fft.fftfreq(arr.shape[1]) * 2.0 * math.pi
    ky = fy[:, None]
    kx = fx[None, :]
    kgrid = np.sqrt(ky * ky + kx * kx)
    band = (kgrid >= float(k_low)) & (kgrid <= float(k_high))
    filtered = np.fft.ifft2(np.fft.fft2(arr_filled) * band).real
    return filtered


def ring_bandpass_lambda(arr: np.ndarray, lambda_min: float, lambda_max: float) -> np.ndarray:
    """Convenience wrapper using real-space wavelengths instead of k."""

    lam_min = max(float(lambda_min), 1e-6)
    lam_max = max(float(lambda_max), lam_min + 1e-6)
    k_low = 2.0 * math.pi / lam_max
    k_high = 2.0 * math.pi / lam_min
    return ring_bandpass(arr, k_low=k_low, k_high=k_high)


def morph_clean(mask: np.ndarray, close_iter: int = 1, open_iter: int = 1) -> np.ndarray:
    """Perform morphology cleaning via closing followed by opening."""

    structure = ndi.generate_binary_structure(2, 1)
    out = mask.astype(bool, copy=False)
    if close_iter > 0:
        out = ndi.binary_closing(out, structure=structure, iterations=int(close_iter))
    if open_iter > 0:
        out = ndi.binary_opening(out, structure=structure, iterations=int(open_iter))
    return out


def make_block_ids(shape: tuple[int, int], block_size: int) -> tuple[np.ndarray, int]:
    """Assign block identifiers for spatial block resampling."""

    h, w = shape
    block = max(1, int(block_size))
    by = (h + block - 1) // block
    bx = (w + block - 1) // block
    ids = np.zeros(shape, dtype=np.int32)
    idx = 0
    for iy in range(by):
        y0 = iy * block
        y1 = min(y0 + block, h)
        for ix in range(bx):
            x0 = ix * block
            x1 = min(x0 + block, w)
            ids[y0:y1, x0:x1] = idx
            idx += 1
    return ids, idx


def build_se_band_info(se_field: np.ndarray, band_specs: Iterable[BandSpec]) -> Dict[str, Dict[str, np.ndarray]]:
    """Pre-compute Σ_e band-pass gradients for re-use across evaluations.

    In addition to gradient components, attaches 'lambda_mean' for angle-kernel scaling.
    """

    out: Dict[str, Dict[str, np.ndarray]] = {}
    for spec in band_specs:
        band = ring_bandpass_lambda(se_field, spec.lambda_min, spec.lambda_max)
        gx = scharr_axis(band, axis=1)
        gy = scharr_axis(band, axis=0)
        mag = np.hypot(gx, gy)
        out[spec.name] = {
            "gx": gx,
            "gy": gy,
            "mag": mag,
            "lambda_mean": float(0.5 * (spec.lambda_min + spec.lambda_max)),
        }
    return out


def build_rr_band_cache(residual_field: np.ndarray, band_specs: Iterable[BandSpec]) -> Dict[str, np.ndarray]:
    """Create band-pass filtered residual caches keyed by band name."""

    cache: Dict[str, np.ndarray] = {}
    for spec in band_specs:
        cache[spec.name] = ring_bandpass_lambda(residual_field, spec.lambda_min, spec.lambda_max)
    return cache


def benjamini_hochberg(p_values: Iterable[float]) -> np.ndarray:
    """Return Benjamini-Hochberg adjusted q-values.

    NaN inputs propagate to NaN outputs.
    """

    p = np.array(list(p_values), dtype=float)
    n = p.size
    if n == 0:
        return np.zeros(0, dtype=float)
    order = np.argsort(p)
    ranks = np.arange(1, n + 1, dtype=float)
    adjusted = np.full(n, np.nan, dtype=float)
    for i, idx in enumerate(order):
        pi = p[idx]
        if not math.isfinite(pi):
            continue
        adjusted[idx] = min(1.0, pi * n / ranks[i])
    # enforce monotonicity from largest rank to smallest
    for i in range(n - 2, -1, -1):
        current_idx = order[i]
        next_idx = order[i + 1]
        ci = adjusted[current_idx]
        ni = adjusted[next_idx]
        if math.isfinite(ci) and math.isfinite(ni):
            adjusted[current_idx] = min(ci, ni)
    return adjusted


class ShadowBandpassEvaluator:
    """Reusable evaluator for band-pass based shadow statistics."""

    def __init__(
        self,
        se_band_info: Mapping[str, Mapping[str, np.ndarray]],
        sn_mask: np.ndarray,
        *,
        block_size: int = 16,
        rr_quantile: float = 0.85,
        morph_close: int = 2,
        morph_open: int = 1,
        morph_clean_min: int = 0,
        angle_gamma: float = 1.0,
        weight_exp: float = 1.0,
        angle_kernel: str = "power",
        vm_kappa: float = 0.0,
        h_cut_pix: float = 0.0,
        chi: float = 1.0,
    ) -> None:
        self.se_band_info = {k: dict(v) for k, v in se_band_info.items()}
        self.sn_mask = sn_mask.astype(bool, copy=False)
        self.block_size = max(1, int(block_size))
        self.rr_quantile = float(rr_quantile)
        self.morph_close = max(0, int(morph_close))
        self.morph_open = max(0, int(morph_open))
        self.morph_clean_min = max(0, int(morph_clean_min))
        # Angle kernel shaping (K(theta; gamma) = sign(-dot)*| -dot |^gamma)
        self.angle_gamma = max(0.1, float(angle_gamma))
        # Gradient magnitude exponent for weighting (w = |∇Σ_e|^weight_exp)
        self.weight_exp = float(weight_exp)
        self.angle_kernel = str(angle_kernel or "power").lower()
        self.vm_kappa = float(vm_kappa)
        self.h_cut_pix = float(h_cut_pix)
        self.chi = float(chi)
        self._block_ids: Optional[np.ndarray] = None
        self._block_count: int = 0

    @property
    def block_ids(self) -> Optional[np.ndarray]:  # pragma: no cover - simple accessor
        return self._block_ids

    @property
    def block_count(self) -> int:  # pragma: no cover - simple accessor
        return self._block_count

    def _ensure_block_ids(self, shape: tuple[int, int]) -> None:
        if self._block_ids is None:
            self._block_ids, self._block_count = make_block_ids(shape, self.block_size)

    def evaluate(
        self,
        rr_band_cache: Mapping[str, np.ndarray],
        mask: np.ndarray,
        *,
        apply_clean: bool = True,
    ) -> Optional[Dict[str, object]]:
        """Compute S_shadow / Q2 metrics for the supplied mask."""

        work_mask = mask.astype(bool, copy=False) & self.sn_mask
        if not np.any(work_mask):
            return None
        if apply_clean:
            if int(np.sum(work_mask)) > self.morph_clean_min:
                work_mask = morph_clean(
                    work_mask,
                    close_iter=self.morph_close,
                    open_iter=self.morph_open,
                )
            else:
                return None
        if not np.any(work_mask):
            return None

        # prepare block ids if needed
        first_band = next(iter(rr_band_cache.values()))
        self._ensure_block_ids(first_band.shape)
        block_weight = np.zeros(self._block_count, dtype=float) if self._block_ids is not None else None
        block_S = np.zeros_like(block_weight) if block_weight is not None else None
        block_Q2 = np.zeros_like(block_weight) if block_weight is not None else None
        block_cos = np.zeros_like(block_weight) if block_weight is not None else None
        block_sin = np.zeros_like(block_weight) if block_weight is not None else None

        total_weight = 0.0
        sum_S = 0.0
        sum_Q2 = 0.0
        sum_cos = 0.0
        sum_sin = 0.0
        sample_count = 0
        band_details: Dict[str, Dict[str, float]] = {}

        for name, se_info in self.se_band_info.items():
            grad_mag = se_info.get("mag")
            if grad_mag is None:
                continue
            valid = work_mask & np.isfinite(grad_mag) & (grad_mag > 1e-6)
            if not np.any(valid):
                continue
            rr_band = rr_band_cache.get(name)
            if rr_band is None:
                continue
            gx_rr = scharr_axis(rr_band, axis=1)
            gy_rr = scharr_axis(rr_band, axis=0)
            mag_rr = np.hypot(gx_rr, gy_rr)
            valid = valid & np.isfinite(mag_rr) & (mag_rr > 1e-6)
            if not np.any(valid):
                continue
            rr_thresh = np.nan
            if math.isfinite(self.rr_quantile):
                try:
                    rr_thresh = float(np.nanquantile(mag_rr[valid], self.rr_quantile))
                except ValueError:
                    rr_thresh = np.nan
            if math.isfinite(rr_thresh):
                valid = valid & (mag_rr >= rr_thresh)
                if not np.any(valid):
                    continue
            # weight pixels by gradient magnitude exponent
            if abs(self.weight_exp - 1.0) < 1e-9:
                weights = grad_mag[valid]
            else:
                with np.errstate(invalid="ignore"):
                    weights = np.power(grad_mag[valid], self.weight_exp)
            if weights.size == 0:
                continue
            gx_se = se_info.get("gx")
            gy_se = se_info.get("gy")
            if gx_se is None or gy_se is None:
                continue
            nx = -gx_se[valid] / (grad_mag[valid] + 1e-12)
            ny = -gy_se[valid] / (grad_mag[valid] + 1e-12)
            rx = gx_rr[valid] / (mag_rr[valid] + 1e-12)
            ry = gy_rr[valid] / (mag_rr[valid] + 1e-12)
            dot = np.clip(nx * rx + ny * ry, -1.0, 1.0)
            det = nx * ry - ny * rx
            theta = np.arctan2(det, dot)
            minus_dot = -dot
            # Apply angle kernel shaping
            if self.angle_kernel == "vonmises":
                # Prefer θ≈π (dot≈-1): w_theta = exp(-kappa_eff * dot)
                lam_mean = float(se_info.get("lambda_mean", 0.0))
                if self.h_cut_pix > 0 and lam_mean > 0:
                    scale = max(0.1, lam_mean / self.h_cut_pix) * max(0.1, self.chi)
                else:
                    scale = max(0.1, self.chi)
                kappa_eff = max(0.0, self.vm_kappa) * scale
                w_theta = np.exp(-kappa_eff * dot)
                # Normalize angle kernel to unit mean over current valid pixels
                # to keep S in [-1, 1] scale. Guard against degenerate cases.
                m_w = float(np.nanmean(w_theta)) if w_theta.size else 1.0
                if not math.isfinite(m_w) or m_w <= 1e-12:
                    m_w = 1.0
                minus_dot = minus_dot * (w_theta / m_w)
            else:
                # sign-preserving power (default)
                if abs(self.angle_gamma - 1.0) > 1e-9:
                    minus_dot = np.sign(minus_dot) * np.power(np.abs(minus_dot), self.angle_gamma)
            # Final safety: confine to [-1, 1] to avoid scale creep
            minus_dot = np.clip(minus_dot, -1.0, 1.0)
            cos_theta = np.cos(theta)
            sin_theta = np.sin(theta)
            cos2_theta = np.cos(2.0 * theta)
            w_sum = float(np.sum(weights))
            if w_sum <= 0:
                continue
            total_weight += w_sum
            sum_S += float(np.sum(weights * minus_dot))
            sum_Q2 += float(np.sum(weights * cos2_theta))
            sum_cos += float(np.sum(weights * cos_theta))
            sum_sin += float(np.sum(weights * sin_theta))
            sample_count += int(weights.size)
            band_details[name] = {
                "S": float(np.sum(weights * minus_dot) / w_sum),
                "Q2": float(np.sum(weights * cos2_theta) / w_sum),
                "weight_sum": w_sum,
                "n": int(weights.size),
            }
            if block_weight is not None and self._block_ids is not None:
                blocks = self._block_ids[valid]
                block_weight += np.bincount(blocks, weights=weights, minlength=self._block_count)
                block_S += np.bincount(blocks, weights=weights * minus_dot, minlength=self._block_count)
                block_Q2 += np.bincount(blocks, weights=weights * cos2_theta, minlength=self._block_count)
                block_cos += np.bincount(blocks, weights=weights * cos_theta, minlength=self._block_count)
                block_sin += np.bincount(blocks, weights=weights * sin_theta, minlength=self._block_count)

        if total_weight <= 0:
            return None
        S_global = sum_S / total_weight
        Q2_global = sum_Q2 / total_weight
        mean_cos = sum_cos / total_weight
        mean_sin = sum_sin / total_weight
        R = math.hypot(mean_cos, mean_sin)
        n_dir = max(sample_count, 1)
        z_rayleigh = n_dir * R * R
        p_rayleigh = math.exp(-z_rayleigh) * (
            1.0 + (2.0 * z_rayleigh - z_rayleigh**2) / (4.0 * n_dir)
        ) if n_dir > 0 else float("nan")
        mu_hat = math.atan2(mean_sin, mean_cos)
        V = R * math.cos(mu_hat)
        z_v = n_dir * V * V
        p_v = math.exp(-z_v) if n_dir > 0 else float("nan")
        contrib: Optional[MutableMapping[str, np.ndarray]] = None
        if block_weight is not None:
            contrib = {
                "weight": block_weight,
                "S": block_S,
                "Q2": block_Q2,
                "cos": block_cos,
                "sin": block_sin,
            }
        return {
            "S": S_global,
            "Q2": Q2_global,
            "band_details": band_details,
            "mask": work_mask,
            "weightsum": total_weight,
            "rayleigh": {"R": R, "z": z_rayleigh, "p": p_rayleigh},
            "v_test": {"V": V, "z": z_v, "p": p_v},
            "n_dir": n_dir,
            "_block_contrib": contrib,
        }
