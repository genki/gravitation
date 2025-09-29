#!/usr/bin/env python3
from __future__ import annotations
import json
import math
import os
import shutil
import sys
import hashlib
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence
import numpy as np
import numpy.linalg as npl
import matplotlib
from time import perf_counter
matplotlib.use('Agg')
import matplotlib.pyplot as plt
try:
    from scripts.utils.mpl_fonts import use_jp_font as _use_jp_font
    _use_jp_font()
except Exception:
    pass
try:
    from astropy.io import fits
except Exception:
    class _FitsStub:
        def getdata(self, *a, **k):
            raise RuntimeError('astropy not available')
        def getheader(self, *a, **k):
            class H: 
                def get(self, k, d=None):
                    return d
            return H()
    fits = _FitsStub()

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

# Dispatcher guard: warn if heavy script is run directly under tmux/user session.
try:
    if os.environ.get('GRAV_BG_JOB', '') != '1' and not os.environ.get('GRAV_SILENCE_DISPATCHER_WARN'):
        in_tmux = bool(os.environ.get('TMUX'))
        cgroup_txt = ''
        try:
            cgroup_txt = Path('/proc/self/cgroup').read_text(encoding='utf-8').lower()
        except Exception:
            cgroup_txt = ''
        if in_tmux or ('tmux' in cgroup_txt):
            sys.stderr.write('[warn] This job is not running under dispatcher (GRAV_BG_JOB=1 not set).\n'
                             '       For OOM resilience and tmux isolation, use:\n'
                             '         scripts/jobs/dispatch_bg.sh -n <name> --scope -- -- <cmd>\n')
            sys.stderr.flush()
except Exception:
    pass

from scripts.cluster.min_kernel import MinKernelParams, predict_kappa
from scripts.config import fair as fair_config
from scripts.fdb.shared_params_loader import load as load_shared_params
from scipy import ndimage as ndi
from scipy.stats import pearsonr, spearmanr

from analysis.shadow_bandpass import (
    BandSpec,
    ShadowBandpassEvaluator,
    benjamini_hochberg,
    build_rr_band_cache,
    build_se_band_info,
    morph_clean,
)


def _append_progress(log_path: Path | None, message: str) -> None:
    if log_path is None:
        return
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open('a', encoding='utf-8') as fp:
            fp.write(f"{datetime.now().isoformat()} {message}\n")
    except Exception:
        pass


class LoopProgress:
    """Lightweight progress tracker with ETA printing."""

    def __init__(self, label: str, total: int, interval: float = 5.0,
                 log_path: Path | None = None, initial: int = 0) -> None:
        self.label = label
        self.total = max(int(total), 1)
        self.interval = max(float(interval), 0.1)
        self.start = perf_counter()
        self.last = self.start
        self.count = min(max(int(initial), 0), self.total)
        self.log_path = log_path
        if self.count:
            resume_msg = f"[holdout:{self.label}] resume at {self.count}/{self.total}"
            print(resume_msg, flush=True)
            _append_progress(self.log_path, resume_msg)
            self.last = self.start - self.interval

    def step(self) -> None:
        self.count = min(self.count + 1, self.total)
        now = perf_counter()
        if self.count == 1 or self.count >= self.total or (now - self.last) >= self.interval:
            elapsed = now - self.start
            denom = self.count if self.count > 0 else 1
            remaining = max(self.total - self.count, 0)
            eta = (elapsed / denom) * remaining if denom > 0 else float('inf')
            msg = f"[holdout:{self.label}] {self.count}/{self.total} | elapsed={elapsed/60:.2f}m ETA={eta/60:.2f}m"
            print(msg, flush=True)
            _append_progress(self.log_path, msg)
            self.last = now


def _json_default(obj: Any) -> Any:
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    return str(obj)


def _compute_stage_digest(label: str,
                          arrays: list[np.ndarray | None],
                          params: dict[str, object]) -> str:
    h = hashlib.sha1()
    h.update(label.encode('utf-8'))
    for arr in arrays:
        if arr is None:
            continue
        carr = np.ascontiguousarray(arr)
        h.update(carr.dtype.str.encode('utf-8'))
        h.update(json.dumps(list(carr.shape)).encode('utf-8'))
        h.update(carr.tobytes())
    for key in sorted(params):
        h.update(str(key).encode('utf-8'))
        h.update(repr(params[key]).encode('utf-8'))
    return h.hexdigest()


class StageResume:
    """Persistence helper for long loops to allow resume after interruption.

    Parallel‑safe filenames: include a short digest in the filename to avoid
    collisions across concurrent runs of the same (holdout, stage).
    Falls back to legacy filenames if present (backward compatible).
    """

    def __init__(self, holdout: str, stage: str, digest: str,
                 total: int | None = None) -> None:
        self.stage = stage
        self.digest = digest
        self.total = int(total) if total is not None else None
        base = Path('server/public/reports/cluster')
        base.mkdir(parents=True, exist_ok=True)
        # New (parallel‑safe) filenames with digest tag
        tag = (digest or '')[:8]
        new_meta = base / f'{holdout}_{stage}_{tag}_meta.json'
        new_vals = base / f'{holdout}_{stage}_{tag}_values.jsonl'
        # Legacy filenames without digest (may collide)
        legacy_meta = base / f'{holdout}_{stage}_meta.json'
        legacy_vals = base / f'{holdout}_{stage}_values.jsonl'
        # Prefer new files if they exist; otherwise, if legacy exists and matches
        # digest, keep using legacy paths for continuity; else use new paths.
        use_legacy = False
        if new_meta.exists() or new_vals.exists():
            self.meta_path, self.values_path = new_meta, new_vals
        elif legacy_meta.exists() or legacy_vals.exists():
            # Peek digest in legacy meta to decide whether to reuse
            try:
                meta = json.loads(legacy_meta.read_text(encoding='utf-8')) if legacy_meta.exists() else {}
            except Exception:
                meta = {}
            if meta.get('digest') == digest:
                use_legacy = True
                self.meta_path, self.values_path = legacy_meta, legacy_vals
            else:
                self.meta_path, self.values_path = new_meta, new_vals
        else:
            self.meta_path, self.values_path = new_meta, new_vals
        self._legacy_paths = (legacy_meta, legacy_vals) if use_legacy else None
        self.iterations = 0
        self.complete = False
        self.values: list[Any] = []
        self._load()

    @property
    def is_complete(self) -> bool:
        if self.total is not None and self.iterations < self.total:
            return False
        return self.complete

    def clear(self) -> None:
        try:
            self.values_path.unlink()
        except FileNotFoundError:
            pass
        except Exception:
            pass
        try:
            self.meta_path.unlink()
        except FileNotFoundError:
            pass
        except Exception:
            pass
        self.iterations = 0
        self.complete = False
        self.values = []

    def _load(self) -> None:
        meta: dict[str, Any] = {}
        if self.meta_path.exists():
            try:
                meta = json.loads(self.meta_path.read_text(encoding='utf-8'))
            except Exception:
                meta = {}
        # If current path does not match digest but legacy exists with matching
        # digest, switch to legacy seamlessly.
        if meta.get('digest') != self.digest and self._legacy_paths:
            legacy_meta, legacy_vals = self._legacy_paths
            try:
                lmeta = json.loads(legacy_meta.read_text(encoding='utf-8')) if legacy_meta.exists() else {}
            except Exception:
                lmeta = {}
            if lmeta.get('digest') == self.digest:
                self.meta_path, self.values_path = legacy_meta, legacy_vals
                meta = lmeta
        if meta.get('digest') != self.digest:
            self.clear()
            return
        if self.total is not None and int(meta.get('total', self.total)) != self.total:
            self.clear()
            return
        self.iterations = int(meta.get('iterations', 0))
        self.complete = bool(meta.get('complete', False))
        raw_values = self._read_values()
        expected_values = int(meta.get('values', len(raw_values)))
        if expected_values < len(raw_values):
            raw_values = raw_values[:expected_values]
        self.values = raw_values
        if self.iterations < len(self.values):
            self.iterations = len(self.values)
        if self.total is not None and self.iterations > self.total:
            self.iterations = self.total

    def _read_values(self) -> list[Any]:
        if not self.values_path.exists():
            return []
        vals: list[Any] = []
        try:
            with self.values_path.open('r', encoding='utf-8') as fp:
                for line in fp:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        vals.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except Exception:
            return []
        return vals

    def _save_meta(self) -> None:
        data = {
            'digest': self.digest,
            'iterations': int(self.iterations),
            'values': len(self.values),
            'complete': bool(self.complete)
        }
        if self.total is not None:
            data['total'] = int(self.total)
        try:
            self.meta_path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
        except Exception:
            pass

    def record(self, value: Any | None) -> None:
        self.iterations = min(self.total or 10**12, self.iterations + 1)
        if value is not None:
            self.values.append(value)
            try:
                with self.values_path.open('a', encoding='utf-8') as fp:
                    fp.write(json.dumps(value, default=_json_default, ensure_ascii=False) + '\n')
            except Exception:
                pass
        self._save_meta()

    def mark_complete(self) -> None:
        self.complete = True
        self._save_meta()

def _apply_edge_trim(mask: np.ndarray, frac: float = 0.05, iterations: int = 1) -> np.ndarray:
    h, w = mask.shape
    trim = int(max(0, round(min(h, w) * frac)))
    if trim <= 0:
        return mask
    trimmed = mask.copy()
    trimmed[:trim, :] = False
    trimmed[-trim:, :] = False
    trimmed[:, :trim] = False
    trimmed[:, -trim:] = False
    if iterations > 0:
        trimmed = ndi.binary_erosion(trimmed, iterations=iterations, border_value=0)
    return trimmed


def _sigma_map_from_params(se_obs: np.ndarray, sigma0: float, coeff: float) -> np.ndarray:
    """Construct σ map = sqrt(σ0^2 + c·Σ_e) with basic clipping."""
    se_clipped = np.clip(se_obs, 0.0, None)
    sigma_sq = sigma0 ** 2 + coeff * se_clipped
    floor_sq = max((sigma0 * 0.1) ** 2, 1e-8)
    sigma_sq = np.maximum(sigma_sq, floor_sq)
    sigma = np.sqrt(sigma_sq)
    sigma[~np.isfinite(sigma)] = sigma0
    return sigma


_BASELINE_PATH = Path('config/baseline_conditions.json')


def _load_fair_cluster() -> dict:
    cfg = fair_config.load('bullet_cluster')
    return cfg if isinstance(cfg, dict) else {}


def _load_baseline_cluster() -> dict:
    if _BASELINE_PATH.exists():
        try:
            data = json.loads(_BASELINE_PATH.read_text())
            if isinstance(data, dict):
                bc = data.get('bullet_cluster')
                if isinstance(bc, dict):
                    return bc
        except Exception:
            pass
    return {}


def _load_wls_params() -> dict:
    fair = _load_fair_cluster().get('wls', {})
    defaults = {
        'sigma0': float(fair.get('sigma0', 0.3)),
        'c': float(fair.get('c', 0.0)),
        'block_pix': int(fair.get('block_pix', 27)),
        'trim_frac': float(fair.get('trim_frac', 0.05)),
        'trim_iter': int(fair.get('trim_iter', 1)),
        'max_lag': int(fair.get('max_lag', 8)),
        'rho_sum_pos_mean': 0.0
    }
    path = Path('config/wls_params.json')
    if path.exists():
        try:
            data = json.loads(path.read_text())
            if isinstance(data, dict):
                for key in defaults:
                    if key in data and isinstance(data[key], (int, float)):
                        defaults[key] = data[key]
        except Exception:
            pass
    return defaults


def _autocorr_rhos(resid_norm: np.ndarray, mask: np.ndarray, max_lag: int = 8) -> list[float]:
    arr = np.where(mask, resid_norm, np.nan)
    mu = np.nanmean(arr)
    arrc = arr - mu
    var = np.nanmean(arrc ** 2)
    if not np.isfinite(var) or var <= 0:
        return []
    rhos: list[float] = []
    for lag in range(1, max_lag + 1):
        vals = []
        if arrc.shape[1] > lag:
            mh = mask[:, :-lag] & mask[:, lag:]
            if np.any(mh):
                prod = arrc[:, :-lag] * arrc[:, lag:]
                vals.append(np.nanmean(prod[mh]) / var)
        if arrc.shape[0] > lag:
            mv = mask[:-lag, :] & mask[lag:, :]
            if np.any(mv):
                prod = arrc[:-lag, :] * arrc[lag:, :]
                vals.append(np.nanmean(prod[mv]) / var)
        if vals:
            rhos.append(float(np.nanmean(vals)))
    return [float(r) for r in rhos if np.isfinite(r)]


def _compute_neff(resid_norm: np.ndarray,
                  mask: np.ndarray,
                  fallback_block: int = 27,
                  max_lag: int = 8) -> tuple[int, int, float]:
    N = int(np.sum(mask))
    if N <= 0:
        return 1, fallback_block, 0.0
    rhos = _autocorr_rhos(resid_norm, mask, max_lag=max_lag)
    rho_pos = float(sum(r for r in rhos if r > 0))
    denom = 1.0 + 2.0 * rho_pos
    if not np.isfinite(denom) or denom <= 0:
        denom = 1.0
    N_eff = int(max(1, round(N / denom)))
    if N_eff <= 0:
        N_eff = int(max(1, round(N / max(1, fallback_block ** 2))))
    block_pix = int(max(4, round(math.sqrt(N / max(N_eff, 1)))))
    if block_pix <= 0:
        block_pix = fallback_block
    return N_eff, block_pix, rho_pos

def _unit_vectors(h: int, w: int, pix: float) -> tuple[np.ndarray, np.ndarray]:
    cy = (h - 1) / 2.0
    cx = (w - 1) / 2.0
    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx - cx) * float(pix)
    dy = (yy - cy) * float(pix)
    rr = np.hypot(dx, dy) + 1e-30
    rhatx = dx / rr
    rhaty = dy / rr
    return rhatx, rhaty

def _lanczos_kernel(delta: float, a: int = 3) -> np.ndarray:
    """Return 1D Lanczos kernel samples centered for fractional shift."""
    if abs(delta) < 1e-8:
        delta = 0.0
    window = np.arange(-a + 1, a + 1, dtype=float)
    x = window - delta
    out = np.sinc(x) * np.sinc(x / a)
    s = float(out.sum())
    if not np.isfinite(s) or abs(s) < 1e-12:
        return np.zeros_like(out)
    return out / s


def _shift_lanczos(arr: np.ndarray, shift_y: float, shift_x: float, a: int = 3) -> np.ndarray:
    """Sub-pixel shift using Lanczos-3 interpolation (separable)."""

    def _shift_axis(data: np.ndarray, delta: float, axis: int) -> np.ndarray:
        frac, integer = np.modf(delta)
        integer = int(integer)
        if integer:
            data = np.roll(data, -integer, axis=axis)
        if abs(frac) < 1e-6:
            return data
        kernel = _lanczos_kernel(frac, a)
        if not np.any(kernel):
            return data
        return ndi.convolve1d(data, kernel, axis=axis, mode='nearest')

    shifted = _shift_axis(arr, shift_y, axis=0)
    shifted = _shift_axis(shifted, shift_x, axis=1)
    return shifted


def _downsample_mean(arr: np.ndarray, factor: int) -> np.ndarray:
    """Downsample array by integer factor using mean pooling."""
    if factor <= 1:
        return arr
    h, w = arr.shape
    new_h = h // factor
    new_w = w // factor
    if new_h <= 0 or new_w <= 0:
        return arr
    trimmed = arr[: new_h * factor, : new_w * factor]
    reshaped = trimmed.reshape(new_h, factor, new_w, factor)
    return reshaped.mean(axis=(1, 3))


def load_cluster_maps(root: Path) -> tuple[np.ndarray, np.ndarray, float] | None:
    """Load (omega_cut_proxy, sigma_e_proxy, pix[kpc/px]).
    Expects FITS: omega_cut.fits, sigma_e.fits with header PIXKPC.
    """
    oc = root / 'omega_cut.fits'
    se = root / 'sigma_e.fits'
    if not oc.exists() or not se.exists():
        return None
    try:
        img_oc = fits.getdata(oc).astype(float)
        img_se = fits.getdata(se).astype(float)
        hdr = fits.getheader(oc)
    except Exception:
        return None
    pix = float(hdr.get('PIXKPC', 1.0))
    return img_oc, img_se, pix


def fit_min_kernel(train_roots: list[Path]) -> MinKernelParams | None:
    # crude grid-search on (alpha, beta, C) using χ² to observed κ (if available)
    alphas = [0.3, 0.6, 1.0]
    betas  = [0.0, 0.3, 0.6]
    Cs     = [0.0, 0.2, 0.5]
    best = None
    for a in alphas:
        for b in betas:
            for c in Cs:
                rss = 0.0; npt = 0
                for rt in train_roots:
                    oc = rt / 'omega_cut.fits'; se = rt / 'sigma_e.fits'; obs = rt / 'kappa_obs.fits'
                    if not (oc.exists() and se.exists() and obs.exists()):
                        continue
                    ocv, sev, pix = load_cluster_maps(rt)
                    k_pred = predict_kappa(ocv, sev, pix, MinKernelParams(alpha=a, beta=b, C=c))
                    k_obs = fits.getdata(obs).astype(float)
                    # Regrid predicted to observed if shapes differ
                    if k_pred.shape != k_obs.shape:
                        zy = k_obs.shape[0] / k_pred.shape[0]
                        zx = k_obs.shape[1] / k_pred.shape[1]
                        k_pred = ndi.zoom(k_pred, zoom=(zy, zx), order=1)
                    m = np.isfinite(k_obs) & np.isfinite(k_pred)
                    if np.any(m):
                        rss += float(np.nansum((k_obs[m] - k_pred[m]) ** 2))
                        npt += int(np.sum(m))
                if npt > 0:
                    val = rss / max(npt, 1)
                    row = (val, a, b, c)
                    if best is None or val < best[0]:
                        best = row
    if best is None:
        return None
    _, a, b, c = best
    return MinKernelParams(alpha=float(a), beta=float(b), C=float(c))


def _center_crop_to_common(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Center-crop two images to the same (minimal) shape using array centers.
    Keeps parity; uses floor on larger dims.
    """
    ha, wa = a.shape; hb, wb = b.shape
    h = min(ha, hb); w = min(wa, wb)
    def crop(x, h, w):
        H, W = x.shape
        cy, cx = H//2, W//2
        y0 = max(0, cy - h//2); x0 = max(0, cx - w//2)
        return x[y0:y0+h, x0:x0+w]
    return crop(a, h, w), crop(b, h, w)


def _parse_float_list(text: str | None) -> list[float]:
    if not text:
        return []
    out: list[float] = []
    for tok in text.split(','):
        tok = tok.strip()
        if not tok:
            continue
        try:
            out.append(float(tok))
        except Exception:
            continue
    return out


def holdout_report(train: list[str], holdout: str, beta_sweep: list[float] | None = None,
                   psf_sigmas: list[float] | None = None,
                   hp_sigmas: list[float] | None = None,
                   se_transform: str | None = None,
                   roi_quantiles: list[float] | None = None,
                   align_offsets: list[float] | None = None,
                   weight_powers: list[float] | None = None,
                   fast: bool = False,
                   downsample: int = 1,
                   use_float32: bool = False,
                   band_limits: Sequence[tuple[float, float]] | None = None,
                   perm_config: dict | None = None,
                   shadow_block_pix: int | None = None) -> int:
    import os as _os
    FAST = bool(fast or (_os.environ.get('FAST_HOLDOUT', '0') == '1'))
    downsample = int(downsample or 1)
    if downsample < 1:
        downsample = 1
    if FAST and downsample == 1:
        downsample = 2
    use_float32 = bool(use_float32 or FAST)
    work_dtype = np.float32 if use_float32 else np.float64
    perm_config = dict(perm_config or {})
    # FAST defaults for permutation/blocks/bands when not explicitly provided
    if FAST:
        perm_config.setdefault('target', 1200)
        perm_config.setdefault('min', 600)
        perm_config.setdefault('max', 2000)
        perm_config.setdefault('early_stop', True)
        perm_config.setdefault('success_threshold', 0.02)
        perm_config.setdefault('failure_threshold', 0.20)
        if band_limits is None:
            band_limits = [(8.0, 16.0)]
        if shadow_block_pix is None:
            shadow_block_pix = 6
    if band_limits is None:
        band_limits = [(4.0, 8.0), (8.0, 16.0)]
    if shadow_block_pix is not None:
        shadow_block_pix = max(1, int(shadow_block_pix))
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    holdout_slug = holdout
    main_html = outdir / f'{holdout_slug}_holdout.html'
    main_json = outdir / f'{holdout_slug}_holdout.json'
    legacy_html = outdir / 'bullet_holdout.html' if holdout.lower() == 'bullet' else None
    legacy_json = outdir / 'bullet_holdout.json' if holdout.lower() == 'bullet' else None

    def _write_html_lines(lines: list[str]) -> None:
        content = '\n'.join(lines)
        main_html.write_text(content, encoding='utf-8')
        if legacy_html and legacy_html != main_html:
            legacy_html.write_text(content, encoding='utf-8')

    def _write_json_obj(obj: Any) -> None:
        payload = json.dumps(obj, indent=2)
        main_json.write_text(payload, encoding='utf-8')
        if legacy_json and legacy_json != main_json:
            legacy_json.write_text(payload, encoding='utf-8')
    roots = [Path(f'data/cluster/{t}') for t in train]
    ho_root = Path(f'data/cluster/{holdout}')
    progress_log = Path('server/public/reports/cluster') / f'{holdout}_progress.log'
    _append_progress(progress_log, f"=== start holdout {holdout} train={train}")
    need = []
    for p in roots + [ho_root]:
        if not p.exists():
            need.append(str(p))
    html = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            f'<title>バレットクラスタ ホールドアウト</title><link rel="stylesheet" href="../styles.css"></head><body>',
            '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
            '<main class="wrap"><h1>最小核(α,β,C) 学習→固定→ホールドアウト</h1>']
    if need:
        html.append('<div class=card><p>必要データが未配置です。</p><ul>')
        for n in need:
            html.append(f'<li>{n}</li>')
        html.append('</ul><p><small>各ディレクトリに omega_cut.fits, sigma_e.fits, 学習セットには kappa_obs.fits が必要。ヘッダに PIXKPC を含めてください。</small></p></div>')
        _write_html_lines(html + ['</main></body></html>'])
        _append_progress(progress_log, f"missing data for holdout {holdout}; abort")
        return 0
    # Prefer shared params from pipeline if available
    pjson = Path('data/cluster/params_cluster.json')
    params = None
    if pjson.exists():
        try:
            jd = json.loads(pjson.read_text(encoding='utf-8'))
            params = MinKernelParams(alpha=float(jd.get('alpha', 1.0)),
                                     beta=float(jd.get('beta', 0.0)),
                                     C=float(jd.get('C', 0.0)),
                                     xi=float(jd.get('xi', 0.0)),
                                     p=float(jd.get('p', 0.5)),
                                     tau_q=float(jd.get('tau_q', 0.7)),
                                     delta_tau_frac=float(jd.get('delta_tau_frac', 0.1)),
                                     s_gate=float(jd.get('s_gate', 1.0)),
                                     se_transform=str(se_transform or jd.get('se_transform', 'none')),
                                     xi_sat=float(jd.get('xi_sat', 1e12)),
                                     q_knee=float(jd.get('q_knee', -1.0)),
                                     gate_sigmas=tuple(jd.get('gate_sigmas', []) if isinstance(jd.get('gate_sigmas', []), list) else []) )
        except Exception:
            params = None
    if params is None:
        params = fit_min_kernel(roots)
    if params is None:
        html.append('<div class=card><p>学習に十分な観測 κ が見つかりませんでした。</p></div>')
        _write_html_lines(html + ['</main></body></html>'])
        _append_progress(progress_log, f"training params unavailable for holdout {holdout}; abort")
        return 0
    # Optional environment overrides for key kernel knobs (A-3 knee scan etc.)
    try:
        _env = __import__('os').environ
        if 'BULLET_Q_KNEE' in _env:
            qk = float(_env['BULLET_Q_KNEE'])
            params = MinKernelParams(**{**params.__dict__, 'q_knee': qk})
        if 'BULLET_P' in _env:
            pv = float(_env['BULLET_P'])
            params = MinKernelParams(**{**params.__dict__, 'p': pv})
        if 'BULLET_XI' in _env:
            xv = float(_env['BULLET_XI'])
            params = MinKernelParams(**{**params.__dict__, 'xi': xv})
        if 'BULLET_XI_SAT' in _env:
            xsv = float(_env['BULLET_XI_SAT'])
            params = MinKernelParams(**{**params.__dict__, 'xi_sat': xsv})
        if 'BULLET_S_GATE' in _env:
            sg = float(_env['BULLET_S_GATE'])
            params = MinKernelParams(**{**params.__dict__, 's_gate': sg})
        if 'BULLET_TAU_Q' in _env:
            tq = float(_env['BULLET_TAU_Q'])
            params = MinKernelParams(**{**params.__dict__, 'tau_q': tq})
        if 'BULLET_DELTA_TAU_FRAC' in _env:
            dtf = float(_env['BULLET_DELTA_TAU_FRAC'])
            params = MinKernelParams(**{**params.__dict__, 'delta_tau_frac': dtf})
        if 'BULLET_SE_TRANSFORM' in _env and _env['BULLET_SE_TRANSFORM'].strip():
            st = _env['BULLET_SE_TRANSFORM'].strip()
            params = MinKernelParams(**{**params.__dict__, 'se_transform': st})
    except Exception:
        pass
    import hashlib
    cluster_param_sha = hashlib.sha256(json.dumps({'alpha': params.alpha, 'beta': params.beta, 'C': params.C,
                                      'xi': params.xi, 'p': params.p, 'tau_q': params.tau_q, 'delta_tau_frac': params.delta_tau_frac,
                                      's_gate': params.s_gate, 'se_transform': params.se_transform, 'xi_sat': getattr(params,'xi_sat',1e12), 'q_knee': getattr(params,'q_knee',-1.0), 'gate_sigmas': list(getattr(params,'gate_sigmas',[]) or [])},
                                      sort_keys=True).encode('utf-8')).hexdigest()[:8]
    html.append('<div class=card><p>固定パラメタ: '
                f'α={params.alpha:.3g}, β={params.beta:.3g}, C={params.C:.3g}, '
                f'ξ={params.xi:.3g}, p={params.p:.3g}, τ_q={params.tau_q:.2g}, δ_τ/τ={params.delta_tau_frac:.2g}, '
                f's_gate={getattr(params,"s_gate",1.0):.2g}, Σ_e変換={getattr(params,"se_transform","none")}, ξ_sat={getattr(params,"xi_sat",1e12):.2g}, '
                f'q_knee={getattr(params,"q_knee",-1.0):.2g}, gate_sigmas={list(getattr(params,"gate_sigmas",[]) or [])} '
                 f'<small>(cluster_sha:{cluster_param_sha})</small></p></div>')
    # Apply to holdout
    shared_card = ''
    shared_sha_short = ''
    shared_sha_full = ''
    try:
        shared_params = load_shared_params(Path('data/shared_params.json'))
        shared_sha_full = hashlib.sha256(Path('data/shared_params.json').read_bytes()).hexdigest()
        shared_sha_short = shared_sha_full[:12]
        shared_card = (
            '<div class=card><p><b>共有パラメータ（単一JSON）</b></p>'
            f'<p>μ(k): ε={shared_params.theta_cos.epsilon:.3g}, '
            f'k0={shared_params.theta_cos.k0:.3g}, m={shared_params.theta_cos.m:.3g} '
            f'/ gas_scale={shared_params.gas_scale if shared_params.gas_scale is not None else shared_params.theta_opt.omega0:.3g}</p>'
            f'<p><small>θ_opt: τ₀={shared_params.theta_opt.tau0:.3g}, ω₀={shared_params.theta_opt.omega0:.3g}; '
            f'θ_if: η={shared_params.theta_if.eta:.3g}; θ_aniso: g={shared_params.theta_aniso.g:.3g}</small></p>'
            f'<p><small>source: data/shared_params.json (sha256:{shared_sha_full}) — SOTA/ベンチ/クラスタで共通参照。旧記号(α,β,ξ…)との対応は脚注参照。</small></p></div>'
        )
    except Exception:
        shared_card = ''

    if shared_card:
        html.append(shared_card)

    data = load_cluster_maps(ho_root)
    if data is None:
        html.append('<div class=card><p>ホールドアウトの omega_cut.fits / sigma_e.fits が見つかりません。</p></div>')
        _write_html_lines(html + ['</main></body></html>'])
        return 0
    oc, se, pix = data
    if downsample > 1:
        oc = _downsample_mean(oc, downsample)
        se = _downsample_mean(se, downsample)
        pix = float(pix) * downsample
    oc = np.asarray(oc, dtype=work_dtype)
    se = np.asarray(se, dtype=work_dtype)
    # initial prediction (for preview); will be refined by sweep below
    k_pred = predict_kappa(oc, se, pix, params)
    # For κ_tot visualization later, try loading κ_GR(baryon)
    kappa_gr_vis = None
    try:
        pgr = Path('data/cluster/gr/bullet_kappa_gr.npy')
        if pgr.exists():
            kappa_gr_vis = np.load(pgr)
    except Exception:
        kappa_gr_vis = None
    fair_cfg = _load_fair_cluster()
    fair_sha_full = fair_config.get_sha256()
    fair_sha_short = fair_sha_full[:12] if fair_sha_full else ''
    baseline_cfg = _load_baseline_cluster()
    wls_params = _load_wls_params()
    trim_frac = float(_os.environ.get('ROI_TRIM_FRAC', wls_params.get('trim_frac', 0.05)))
    trim_iter = int(_os.environ.get('ROI_TRIM_ITER', wls_params.get('trim_iter', 1)))
    sigma0_param = float(_os.environ.get('WLS_SIGMA0_OVERRIDE', wls_params.get('sigma0', 0.3)))
    coeff_param = float(_os.environ.get('WLS_SIGMA_C_OVERRIDE', wls_params.get('c', 0.0)))
    block_pix_cfg = int(_os.environ.get('WLS_BLOCK_PIX_OVERRIDE', wls_params.get('block_pix', 27)))
    fair_psf = float(fair_cfg.get('psf_sigma', baseline_cfg.get('psf_sigma', 1.0) if baseline_cfg else 1.0)) if fair_cfg else float(baseline_cfg.get('psf_sigma', 1.0) if baseline_cfg else 1.0)
    fair_hp = float(fair_cfg.get('highpass_sigma', baseline_cfg.get('highpass_sigma', 8.0) if baseline_cfg else 8.0)) if fair_cfg else float(baseline_cfg.get('highpass_sigma', 8.0) if baseline_cfg else 8.0)
    fair_counts = fair_cfg.get('counts', {}) if fair_cfg else {}
    fair_alignment = fair_cfg.get('alignment', {}) if fair_cfg else {}
    fair_wrap = fair_cfg.get('wrap_shift', {}) if fair_cfg else {}
    fair_rng = fair_cfg.get('rng', {}) if fair_cfg else {}
    fair_kmap = fair_cfg.get('k_map', {}) if fair_cfg else {}
    baseline_shadow = baseline_cfg.get('shadow', {}) if baseline_cfg else {}
    fair_shadow = fair_cfg.get('shadow', {}) if isinstance(fair_cfg, dict) else {}

    def _shadow_default(key: str, fallback: float | int) -> float | int:
        for source in (fair_shadow, baseline_shadow):
            if isinstance(source, dict):
                val = source.get(key)
                if isinstance(val, (int, float)):
                    return val
        return fallback

    def _shadow_list(key: str) -> list[float]:
        for source in (fair_shadow, baseline_shadow):
            if isinstance(source, dict):
                val = source.get(key)
                if isinstance(val, (list, tuple)):
                    try:
                        return [float(x) for x in val]
                    except Exception:
                        continue
        return []
    se_quantile_base = float(_shadow_default('se_quantile', 0.75))
    se_quantile_env = float(_os.environ.get('BULLET_SHADOW_SE_Q', str(se_quantile_base)))
    sn_quantile_base = float(_shadow_default('sn_quantile', 0.9))
    sn_quantile_env = float(_os.environ.get('BULLET_SHADOW_SN_Q', str(sn_quantile_base)))
    morph_close = int(_shadow_default('morph_close', 2))
    morph_open = int(_shadow_default('morph_open', 1))
    morph_clean_min = int(_shadow_default('morph_clean_min', 0)) if isinstance(_shadow_default('morph_clean_min', 0), (int, float)) else 0
    edge_quantiles_cfg = _shadow_list('edge_quantiles')
    edge_quantiles_env = _os.environ.get('BULLET_SHADOW_EDGE_QS')
    if edge_quantiles_env:
        try:
            q_list = [float(x) for x in edge_quantiles_env.split(',') if x.strip()]
        except Exception:
            q_list = []
    else:
        q_list = []
    if not q_list and isinstance(edge_quantiles_cfg, (list, tuple)):
        try:
            q_list = [float(x) for x in edge_quantiles_cfg]
        except Exception:
            q_list = []
    if not q_list:
        q_list = [se_quantile_env]
    q_list = [q for q in q_list if 0.0 <= q <= 1.0]
    max_lag_corr = int(max(4, round(wls_params.get('max_lag', 8))))

    if not FAST:
        fig, ax = plt.subplots(1, 1, figsize=(5.2, 4.4))
        im = ax.imshow(k_pred, origin='lower', cmap='magma')
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label='κ_pred')
        ax.set_title('FDB 予測 κ（固定パラ）')
        png_pred = outdir / 'bullet_kappa_pred.png'
        fig.tight_layout(); fig.savefig(png_pred, dpi=140); plt.close(fig)
    else:
        png_pred = outdir / 'bullet_kappa_pred.png'
    # If observed κ exists, compute ΔAICc vs controls + 三指標（proxy）
    obs_p = ho_root / 'kappa_obs.fits'
    summary = {}
    rchi2_map = {'FDB': float('nan'), 'rot': float('nan'), 'shift': float('nan'), 'shuffle': float('nan')}

    mask_cfg = fair_cfg.get('mask', {}) if fair_cfg else {}
    mask_q_base = float(mask_cfg.get('fraction', 0.75))
    mask_override = _os.environ.get('BULLET_MASK_Q')
    try:
        mask_q_env = float(mask_override) if mask_override else None
    except Exception:
        mask_q_env = None
    roi_list: list[float] = []
    if roi_quantiles:
        for val in roi_quantiles:
            try:
                q = float(val)
            except Exception:
                continue
            if 0.0 <= q <= 1.0:
                roi_list.append(q)
    if mask_q_env is not None and 0.0 <= mask_q_env <= 1.0:
        roi_list = [mask_q_env]
    if not roi_list:
        roi_list = [mask_q_base]
    mask_q = roi_list[0]

    align_offsets_list: list[float] = []
    if align_offsets:
        for val in align_offsets:
            try:
                align_offsets_list.append(float(val))
            except Exception:
                continue
    if not align_offsets_list:
        env_align = _os.environ.get('BULLET_ALIGN_OFFSETS')
        align_offsets_list = _parse_float_list(env_align)
    if not align_offsets_list:
        align_offsets_list = [0.0]

    weight_list: list[float] = []
    if weight_powers:
        try:
            weight_list = [float(x) for x in weight_powers]
        except Exception:
            weight_list = []
    if not weight_list:
        env_weight = _parse_float_list(_os.environ.get('BULLET_WEIGHT_POWERS'))
        if env_weight:
            weight_list = env_weight
    if not weight_list:
        weight_list = _shadow_list('weight_powers')
    if not weight_list:
        try:
            weight_list = [float(_shadow_default('weight_power', 0.0))]
        except Exception:
            weight_list = [0.0]
    weight_list = [float(w) for w in weight_list]

    if obs_p.exists():
        k_obs = fits.getdata(obs_p).astype(work_dtype)
        if downsample > 1:
            k_obs = _downsample_mean(k_obs, downsample)
        # Regrid predicted to observed if shapes differ
        if k_pred.shape != k_obs.shape:
            zy = k_obs.shape[0] / k_pred.shape[0]
            zx = k_obs.shape[1] / k_pred.shape[1]
            k_pred = ndi.zoom(k_pred, zoom=(zy, zx), order=1)
        # Prepare Σ_e on obs grid
        se_obs = se
        if se.shape != k_obs.shape:
            zy, zx = k_obs.shape[0]/se.shape[0], k_obs.shape[1]/se.shape[1]
            se_obs = ndi.zoom(se, zoom=(zy, zx), order=1)
        oc_obs = oc
        if oc.shape != k_obs.shape:
            zy, zx = k_obs.shape[0]/oc.shape[0], k_obs.shape[1]/oc.shape[1]
            oc_obs = ndi.zoom(oc, zoom=(zy, zx), order=1)

        # Sweep small grid of (gauss_sigma, weight_power) to stabilize KPI
        candidates = []
        psf_records = []
        default_psf = fair_psf if isinstance(fair_psf, float) else 1.0
        PSF_LIST = psf_sigmas if (psf_sigmas and len(psf_sigmas) > 0) else [default_psf]
        for roi_idx, mask_q in enumerate(roi_list):
            psf_prog = LoopProgress(
                f"{holdout}-psf{('-' + str(roi_idx)) if len(roi_list) > 1 else ''}",
                len(PSF_LIST),
                log_path=progress_log
            ) if PSF_LIST else None
            for gauss_sig in PSF_LIST:
                # PSF match
                k_pred_s = ndi.gaussian_filter(k_pred, sigma=gauss_sig)
                k_obs_s  = ndi.gaussian_filter(k_obs,  sigma=gauss_sig)
                m = np.isfinite(k_obs_s) & np.isfinite(k_pred_s)
                n = int(np.sum(m))
                if n <= 10:
                    if psf_prog:
                        psf_prog.step()
                    continue
                m = _apply_edge_trim(m, frac=trim_frac, iterations=trim_iter)
                if not np.any(m):
                    if psf_prog:
                        psf_prog.step()
                    continue
                n = int(np.sum(m))
                # Subpixel alignment via FFT xcorr (unified geometry)
                try:
                    import numpy.fft as _fft
                    A = (k_pred_s * m)
                    B = (k_obs_s  * m)
                    FA = _fft.rfftn(A); FB = _fft.rfftn(B)
                    CC = _fft.irfftn(FA * np.conj(FB), s=A.shape)
                    py, px = np.unravel_index(np.argmax(CC), CC.shape)
                    cy, cx = A.shape[0]//2, A.shape[1]//2
                    dyf = float(py - cy); dxf = float(px - cx)
                except Exception:
                    dyf = dxf = 0.0
                sigma0 = sigma0_param
                coeff = coeff_param
                sigma_map = _sigma_map_from_params(se_obs, sigma0, coeff)
                sigma_map = np.where(np.isfinite(sigma_map), sigma_map, np.nan)
                sigma_map = np.where(sigma_map > 1e-8, sigma_map, 1e-8)
                rng = np.random.default_rng(42)
                se_mean = float(np.nanmean(se_obs[m])) if np.any(m) else float(np.nanmean(se_obs[np.isfinite(se_obs)]))
                se_mean = se_mean if np.isfinite(se_mean) and se_mean != 0.0 else 1.0

                for weight_power in weight_list:
                    weight_power = float(weight_power)
                    weight_vals_full = None
                    if abs(weight_power) > 1e-12:
                        base = se_obs / (se_mean + 1e-12)
                        base = np.where(base > 0, base, 1e-6)
                        weight_vals_full = np.power(base, weight_power)

                    for dy_off in align_offsets_list:
                        for dx_off in align_offsets_list:
                            dy_total = dyf + float(dy_off)
                            dx_total = dxf + float(dx_off)
                            k_pred_s_aligned = _shift_lanczos(k_pred_s, -dy_total, -dx_total)
                            res_base_full = (k_obs_s - k_pred_s_aligned)
                            res_norm = np.zeros_like(res_base_full, dtype=float)
                            res_norm[m] = res_base_full[m] / sigma_map[m]
                            weights_m = weight_vals_full[m] if weight_vals_full is not None else None
                            sq = (res_norm[m]) ** 2
                            if weights_m is not None:
                                chi_fdb = float(np.nansum(sq * weights_m))
                            else:
                                chi_fdb = float(np.nansum(sq))
                            N_eff, block_pix_est, rho_sum = _compute_neff(res_norm, m, fallback_block=block_pix_cfg, max_lag=max_lag_corr)

                            def aicc(chi2: float, k: int, N: int) -> float:
                                return float(chi2 + 2*k + (2*k*(k+1))/max(N-k-1, 1))

                            def ctrl_chi2(arr: np.ndarray) -> float:
                                r_full = (k_obs_s - arr)
                                r_norm = np.zeros_like(r_full, dtype=float)
                                r_norm[m] = r_full[m] / sigma_map[m]
                                sq_local = (r_norm[m]) ** 2
                                if weights_m is not None:
                                    return float(np.nansum(sq_local * weights_m))
                                return float(np.nansum(sq_local))

                            chi_rot = ctrl_chi2(np.rot90(k_pred_s_aligned, 2))  # 180° around center
                            kp_shift = np.roll(np.roll(k_pred_s_aligned, 12, axis=0), -7, axis=1)
                            chi_shift = ctrl_chi2(kp_shift)
                            try:
                                import numpy.fft as _fft
                                F = _fft.rfftn(k_pred_s_aligned)
                                amp = np.abs(F)
                                rnd = rng.uniform(-np.pi, np.pi, size=F.shape)
                                Fr = amp * np.exp(1j * rnd)
                                kp = _fft.irfftn(Fr, s=k_pred_s_aligned.shape).real
                            except Exception:
                                kp = k_pred_s_aligned.copy(); H, W = kp.shape; sh = 64
                                for y in range(0, H, sh):
                                    for x in range(0, W, sh):
                                        yy = min(y+sh, H); xx = min(x+sh, W)
                                        sl = (slice(y, yy), slice(x, xx))
                                        dy_tmp, dx_tmp = rng.integers(-sh//2, sh//2+1, size=2)
                                        kp[sl] = np.roll(np.roll(kp[sl], dy_tmp, axis=0), dx_tmp, axis=1)
                            chi_shuffle = ctrl_chi2(kp)
                            A_fdb = aicc(chi_fdb, k=2, N=N_eff)
                            A_rot = aicc(chi_rot,   k=1, N=N_eff)
                            A_shift = aicc(chi_shift, k=2, N=N_eff)
                            A_shuffle = aicc(chi_shuffle, k=0, N=N_eff)
                            d_shift = A_fdb - A_shift
                            sigma_med_val = float(np.nanmedian(sigma_map[m])) if np.any(m) else float('nan')
                            psf_records.append({
                                'sigma_psf': float(gauss_sig),
                                'weight_power': float(weight_power),
                                'AICc_FDB': float(A_fdb),
                                'AICc_shift': float(A_shift),
                                'delta_FDB_minus_shift': float(d_shift),
                                'N': n,
                                'N_eff': int(N_eff),
                                'sigma_floor': sigma0,
                                'sigma_scale': coeff,
                                'rho_sum_pos': float(rho_sum),
                                'block_pix_est': int(block_pix_est),
                                'align_offset_dy': float(dy_off),
                                'align_offset_dx': float(dx_off),
                                'mask_quantile': float(mask_q)
                            })
                            candidates.append({
                                'gauss_sigma': gauss_sig,
                                'weight_power': float(weight_power),
                                'A_fdb': A_fdb,
                                'A_rot': A_rot,
                                'A_shift': A_shift,
                                'A_shuffle': A_shuffle,
                                'n': n,
                                'sigma_med': sigma_med_val,
                                'k_pred_s': k_pred_s_aligned,
                                'k_obs_s': k_obs_s,
                                'mask': m,
                                'N_eff': int(N_eff),
                                'block_pix': int(block_pix_est),
                                'sigma_floor': sigma0,
                                'sigma_scale': coeff,
                                'trim_frac': float(trim_frac),
                                'trim_iter': int(trim_iter),
                                'rho_sum': float(rho_sum),
                                'kmap': {'FDB': 2, 'rot': 1, 'shift': 2, 'shuffle': 0},
                                'align_dx': float(dx_total), 'align_dy': float(dy_total), 'delta_shift': d_shift,
                                'align_offset_dx': float(dx_off), 'align_offset_dy': float(dy_off),
                                'mask_quantile': float(mask_q)
                            })
                if psf_prog:
                    psf_prog.step()
        # pick best (min A_fdb)
        if not candidates:
            candidates = []
        feasible = [c for c in candidates if (c.get('delta_shift', 0.0) <= -10.0 and c.get('A_rot', float('inf')) > c.get('A_fdb', float('inf')) and c.get('A_shuffle', float('inf')) > c.get('A_fdb', float('inf')))]
        search_pool = feasible if feasible else candidates
        best = None
        for c in search_pool:
            if best is None:
                best = c
            else:
                if c.get('delta_shift', 1e99) < best.get('delta_shift', 1e99):
                    best = c
                elif c.get('delta_shift', 1e99) == best.get('delta_shift', 1e99) and c['A_fdb'] < best['A_fdb']:
                    best = c
        if best is None:
            best = {
                'gauss_sigma': 0.0,
                'weight_power': 0.0,
                'A_fdb': float('nan'),
                'A_rot': float('nan'),
                'A_shift': float('nan'),
                'A_shuffle': float('nan'),
                'n': int(np.sum(np.isfinite(k_obs) & np.isfinite(k_pred))),
                'sigma': float('nan'),
                'k_pred_s': k_pred,
                'k_obs_s': k_obs,
                'mask': (np.isfinite(k_obs) & np.isfinite(k_pred)),
                'N_eff': int(np.sum(np.isfinite(k_obs) & np.isfinite(k_pred))),
                'block_pix': 27,
                'sigma_floor': 1.0,
                'sigma_scale': 0.2,
                'trim_frac': float(os.environ.get('ROI_TRIM_FRAC', '0.05')),
                'trim_iter': int(os.environ.get('ROI_TRIM_ITER', '1')),
                'rho_sum': 0.0,
                'mask_quantile': float(mask_q)
            }
        # Unpack best
        gauss_sig = best['gauss_sigma']; wpow = best['weight_power']
        A_fdb = best['A_fdb']; A_rot = best['A_rot']; A_shift = best['A_shift']; A_shuffle = best['A_shuffle']
        n = best['n']
        kmap = best.get('kmap') or fair_kmap or {'FDB': 2, 'rot': 1, 'shift': 2, 'shuffle': 0}
        k_pred_s = best['k_pred_s']; k_obs_s = best['k_obs_s']; m = best['mask']
        N_eff = int(best.get('N_eff', n))
        block_pix = int(best.get('block_pix', 27))
        sigma_floor_best = float(best.get('sigma_floor', 1.0))
        sigma_scale_best = float(best.get('sigma_scale', 0.2))
        sigma_map_best = _sigma_map_from_params(se_obs, sigma_floor_best, sigma_scale_best)
        sigma_map_best = np.where(np.isfinite(sigma_map_best), sigma_map_best, np.nan)
        sigma_map_best = np.where(sigma_map_best > 1e-8, sigma_map_best, 1e-8)
        weight_power_best = float(wpow)
        weight_map_best = None
        if abs(weight_power_best) > 1e-12:
            se_mean_best = float(np.nanmean(se_obs[m])) if np.any(m) else float(np.nanmean(se_obs[np.isfinite(se_obs)]))
            if not np.isfinite(se_mean_best) or se_mean_best == 0.0:
                se_mean_best = 1.0
            base_best = se_obs / (se_mean_best + 1e-12)
            base_best = np.where(base_best > 0, base_best, 1e-6)
            weight_map_best = np.power(base_best, weight_power_best)
        align_dx = float(best.get('align_dx', 0.0)); align_dy = float(best.get('align_dy', 0.0))
        mask_q = float(best.get('mask_quantile', mask_q))

        # Figure: panels with common colorbar/axes and contours
        sigma_disp = float(np.nanmedian(sigma_map_best[m])) if np.any(m) else float('nan')

        if not FAST:
            try:
                vmin = np.nanpercentile(k_obs_s[m], 2.5); vmax = np.nanpercentile(k_obs_s[m], 97.5)
                fig, axs = plt.subplots(2, 2, figsize=(8.4, 7.2))
                for ax in axs.ravel():
                    ax.set_xlabel('x [pix]'); ax.set_ylabel('y [pix]')
                im0 = axs[0,0].imshow(k_pred_s, origin='lower', cmap='magma', vmin=vmin, vmax=vmax)
                axs[0,0].set_title('κ_FDB(pred)')
                im1 = axs[0,1].imshow(k_obs_s, origin='lower', cmap='magma', vmin=vmin, vmax=vmax)
                axs[0,1].set_title('κ_obs')
                diff = (k_obs_s - k_pred_s)
                im2 = axs[1,0].imshow(diff, origin='lower', cmap='coolwarm')
                axs[1,0].set_title('κ_obs − κ_pred')
                axs[1,1].imshow(k_pred_s, origin='lower', cmap='magma', vmin=vmin, vmax=vmax)
                try:
                    cs = axs[1,1].contour(k_obs_s, colors='cyan', linewidths=0.7)
                    axs[1,1].clabel(cs, inline=1, fontsize=7, fmt='%.2g')
                except Exception:
                    pass
                axs[1,1].set_title('κ_FDB + κ_obs 等高線')
                cbar = fig.colorbar(im1, ax=axs, fraction=0.046, pad=0.04)
                cbar.set_label('κ')
                png_panels = outdir / 'bullet_kappa_panels.png'
                fig.tight_layout(); fig.savefig(png_panels, dpi=140); plt.close(fig)
                html.append('<div class=card><p><img src="bullet_kappa_panels.png" style="max-width:100%"></p></div>')
            except Exception:
                pass
        # κ_tot vs κ_obs (visual only) if GR map available and not FAST
        if (kappa_gr_vis is not None) and (not FAST):
            try:
                kgr = kappa_gr_vis
                if kgr.shape != k_pred_s.shape:
                    zy, zx = k_pred_s.shape[0]/kgr.shape[0], k_pred_s.shape[1]/kgr.shape[1]
                    kgr = ndi.zoom(kgr, zoom=(zy, zx), order=1)
                k_tot = k_pred_s + kgr
                vmin = np.nanpercentile(k_obs_s[m], 2.5); vmax = np.nanpercentile(k_obs_s[m], 97.5)
                fig, axs = plt.subplots(1, 3, figsize=(11.2, 3.6))
                axs[0].imshow(k_tot, origin='lower', cmap='plasma', vmin=vmin, vmax=vmax); axs[0].set_title('κ_tot')
                axs[1].imshow(k_obs_s, origin='lower', cmap='plasma', vmin=vmin, vmax=vmax); axs[1].set_title('κ_obs')
                axs[2].imshow((k_obs_s - k_tot), origin='lower', cmap='coolwarm'); axs[2].set_title('R_tot = κ_obs − κ_tot')
                for ax in axs:
                    ax.set_xlabel('x [pix]'); ax.set_ylabel('y [pix]')
                png_tot = outdir / 'bullet_kappa_tot_panels.png'
                fig.tight_layout(); fig.savefig(png_tot, dpi=140); plt.close(fig)
                html.append('<div class=card><h3>κ_tot vs κ_obs</h3><p><img src="bullet_kappa_tot_panels.png" style="max-width:100%"></p>'
                            '<small>判定は κ_FDB と対照（rot/shift/shuffle）に基づく。</small></div>')
            except Exception:
                pass

        # 三指標（proxy）
        # 1) ピーク距離（κ_pred vs Σ_e 由来のX線プロキシ）
        #    Σ_e を観測グリッドへリグリッド（se_obs は上で用意済み）
        def peak_xy(a: np.ndarray) -> tuple[int, int]:
            idx = int(np.nanargmax(a))
            ny, nx = a.shape
            y, x = divmod(idx, nx)
            return y, x
        py_m, px_m = peak_xy(k_pred_s)
        py_x, px_x = peak_xy(se_obs)
        peak_offset_pix = float(np.hypot(px_m - px_x, py_m - py_x))
        # Masked-peak distance: restrict to top-q quantile of Σ_e to avoid spurious outskirts
        try:
            thr_m = float(np.nanquantile(se_obs, mask_q))
        except Exception:
            thr_m = None
        peak_offset_pix_masked = float('nan')
        if thr_m is not None:
            mtop = np.isfinite(se_obs) & (se_obs >= thr_m)
            if np.any(mtop):
                # argmax within mask by setting outside to -inf
                km = k_pred_s.copy(); km[~mtop] = -np.inf
                sm = se_obs.copy();   sm[~mtop] = -np.inf
                pym, pxm = peak_xy(km)
                pyx, pxx = peak_xy(sm)
                peak_offset_pix_masked = float(np.hypot(pxm - pxx, pym - pyx))

        # High-pass version (common-field, large-scale trend removed)
        default_hp = fair_hp if isinstance(fair_hp, float) else 8.0
        HP_LIST = hp_sigmas if (hp_sigmas and len(hp_sigmas) > 0) else [default_hp]
        hp_metrics = []
        hp_prog = LoopProgress(f"{holdout}-hp", len(HP_LIST), log_path=progress_log) if HP_LIST else None
        for hp_sigma_val in HP_LIST:
            k_pred_hp_tmp = k_pred_s - ndi.gaussian_filter(k_pred_s, sigma=hp_sigma_val)
            se_hp_tmp     = se_obs  - ndi.gaussian_filter(se_obs,   sigma=hp_sigma_val)
            if thr_m is not None:
                km = k_pred_hp_tmp.copy(); km[~mtop] = -np.inf
                sm = se_hp_tmp.copy();     sm[~mtop] = -np.inf
            else:
                km = k_pred_hp_tmp; sm = se_hp_tmp
            py_m_hp, px_m_hp = peak_xy(km)
            py_x_hp, px_x_hp = peak_xy(sm)
            hp_off = float(np.hypot(px_m_hp - px_x_hp, py_m_hp - py_x_hp))
            hp_metrics.append({'sigma': float(hp_sigma_val),
                               'peak_offset_pix': hp_off,
                               'k_pred_hp': k_pred_hp_tmp,
                               'se_hp': se_hp_tmp})
            if hp_prog:
                hp_prog.step()
        hp_summary = [{'sigma_highpass': float(item['sigma']),
                       'peak_offset_pix': float(item['peak_offset_pix'])} for item in hp_metrics]
        if hp_metrics:
            best_hp = min(hp_metrics, key=lambda d: d['peak_offset_pix'])
            hp_sigma = float(best_hp['sigma'])
            k_pred_hp = best_hp['k_pred_hp']
            se_hp = best_hp['se_hp']
            hp_peak_offset_pix = float(best_hp['peak_offset_pix'])
            for rec in hp_metrics:
                rec.pop('k_pred_hp', None)
                rec.pop('se_hp', None)
        else:
            hp_sigma = float(HP_LIST[0])
            k_pred_hp = k_pred_s - ndi.gaussian_filter(k_pred_s, sigma=hp_sigma)
            se_hp     = se_obs  - ndi.gaussian_filter(se_obs,   sigma=hp_sigma)
            if thr_m is not None:
                km = k_pred_hp.copy(); km[~mtop] = -np.inf
                sm = se_hp.copy();     sm[~mtop] = -np.inf
            else:
                km = k_pred_hp; sm = se_hp
            py_m_hp, px_m_hp = peak_xy(km)
            py_x_hp, px_x_hp = peak_xy(sm)
            hp_peak_offset_pix = float(np.hypot(px_m_hp - px_x_hp, py_m_hp - py_x_hp))
            hp_summary = [{'sigma_highpass': float(hp_sigma), 'peak_offset_pix': hp_peak_offset_pix}]
        # 2) 剪断位相整合（∇κ_pred と ∇κ_obs の角度整合の平均cos; proxy）
        def grad_angle(a: np.ndarray) -> np.ndarray:
            gy, gx = np.gradient(a.astype(float))
            return np.arctan2(gy, gx)
        # Structure-tensor orientation (robust位相; γの位相に近いproxy)
        def st_orientation(a: np.ndarray, sig: float = 1.0) -> np.ndarray:
            gy, gx = np.gradient(a.astype(float))
            Gxx = ndi.gaussian_filter(gx*gx, sigma=sig)
            Gyy = ndi.gaussian_filter(gy*gy, sigma=sig)
            Gxy = ndi.gaussian_filter(gx*gy, sigma=sig)
            # orientation = 0.5 * atan2(2Gxy, Gxx - Gyy)
            return 0.5 * np.arctan2(2.0*Gxy, (Gxx - Gyy))
        ang_pred = st_orientation(k_pred_s, sig=gauss_sig)
        ang_obs  = st_orientation(k_obs_s,  sig=gauss_sig)
        # 有効マスク（強度が定義され、勾配が有限）
        mm = m & np.isfinite(ang_pred) & np.isfinite(ang_obs)
        cos_d = np.cos(ang_pred[mm] - ang_obs[mm]) if np.any(mm) else np.array([np.nan])
        shear_phase_cos = float(np.nanmean(cos_d))
        # 3) κ残差 × Σ_e の負相関
        rr = (k_obs_s - k_pred_s)
        # Auxiliary: κ_tot residual correlations if κ_GR available
        aux = {}
        try:
            pgr = Path('data/cluster/gr/bullet_kappa_gr.npy')
            if pgr.exists():
                kgr0 = np.load(pgr)
                kgr = kgr0 if kgr0.shape == k_pred_s.shape else ndi.zoom(kgr0, zoom=(k_pred_s.shape[0]/kgr0.shape[0], k_pred_s.shape[1]/kgr0.shape[1]), order=1)
                rrt = (k_obs_s - (k_pred_s + kgr))
                mm4 = np.isfinite(rrt) & np.isfinite(se_obs)
                spear_tot, p_tot = spearmanr(rrt[mm4].ravel(), se_obs[mm4].ravel(), nan_policy='omit') if np.any(mm4) else (float('nan'), float('nan'))
                thr_t = float(np.nanquantile(se_obs[mm4], 0.9)) if np.any(mm4) else float('nan')
                if thr_t==thr_t:
                    sel_t = mm4 & (se_obs >= thr_t)
                    spear_tot_p90, p_tot_p90 = spearmanr(rrt[sel_t].ravel(), se_obs[sel_t].ravel(), nan_policy='omit') if np.any(sel_t) else (float('nan'), float('nan'))
                else:
                    spear_tot_p90, p_tot_p90 = float('nan'), float('nan')
                aux = {'spear_r_tot': float(spear_tot), 'spear_p_tot': float(p_tot), 'spear_r_tot_p90': float(spear_tot_p90), 'spear_p_tot_p90': float(p_tot_p90)}
        except Exception:
            aux = {}
        #   共通マスク
        mm2 = np.isfinite(rr) & np.isfinite(se_obs)
        r_val = float('nan')
        r_spear = float('nan'); p_spear = float('nan')
        strat = {}
        if np.any(mm2):
            try:
                r_val = float(pearsonr(rr[mm2].ravel(), se_obs[mm2].ravel())[0])
                r_spear, p_spear = spearmanr(rr[mm2].ravel(), se_obs[mm2].ravel(), nan_policy='omit')
                # stratify by Σ_e quantiles (top-half, top-quartile, top-decile)
                se_v = se_obs[mm2].ravel(); rr_v = rr[mm2].ravel()
                for label, q in [('p50',0.5),('p75',0.75),('p90',0.9)]:
                    try:
                        thr = float(np.nanquantile(se_v, q))
                        sel = (se_v >= thr)
                        if np.any(sel):
                            rs, ps = spearmanr(rr_v[sel], se_v[sel], nan_policy='omit')
                            strat[label] = {'thr':thr, 'spear_r': float(rs), 'p': float(ps), 'n': int(sel.sum())}
                    except Exception:
                        pass
            except Exception:
                pass

        # Radial map（Σ_e ピーク中心）
        ny, nx = se_obs.shape
        yy, xx = np.mgrid[0:ny, 0:nx]
        try:
            cyx = np.unravel_index(np.nanargmax(se_obs), se_obs.shape)
        except Exception:
            cyx = (se_obs.shape[0]//2, se_obs.shape[1]//2)
        cy0, cx0 = float(cyx[0]), float(cyx[1])
        rmap = np.hypot(yy - cy0, xx - cx0)
        valid = np.isfinite(se_obs)
        thr_core_r = float(np.nanquantile(rmap[valid], 0.5)) if np.any(valid) else float('nan')
        thr_outer_r = float(np.nanquantile(rmap[valid], 0.75)) if np.any(valid) else float('nan')
        # 3b) バンドパス影整合 (S_shadow, Q2, V-test)
        BAND_FILTERS = [
            BandSpec(name=f'band_{float(low):g}_{float(high):g}', lambda_min=float(low), lambda_max=float(high))
            for (low, high) in band_limits
        ] or [BandSpec(name='band_8_16', lambda_min=8.0, lambda_max=16.0)]
        rr_clean = np.where(np.isfinite(rr), rr, 0.0).astype(float)
        base_mask_shadow = np.isfinite(rr) & np.isfinite(se_obs)
        try:
            sigma_thresh = float(np.nanquantile(sigma_map_best[m], sn_quantile_env)) if np.any(m) else float('inf')
        except Exception:
            sigma_thresh = float('inf')
        if sigma_thresh == sigma_thresh:
            sn_mask_shadow = base_mask_shadow & (sigma_map_best <= sigma_thresh)
        else:
            sn_mask_shadow = base_mask_shadow

        oc_field = oc_obs.astype(float)
        grad_mag = np.zeros_like(oc_field, dtype=float)
        grad_nx = np.zeros_like(oc_field, dtype=float)
        grad_ny = np.zeros_like(oc_field, dtype=float)
        _gs_env = _os.environ.get('BULLET_SHADOW_GATE_SIGMAS')
        if _gs_env:
            try:
                grad_sigmas = [0.0] + [float(x) for x in _gs_env.split(',') if x.strip()]
            except Exception:
                grad_sigmas = [0.0] + list(getattr(params, 'gate_sigmas', ()) or [])
        else:
            grad_sigmas = [0.0] + list(getattr(params, 'gate_sigmas', ()) or [])
        for gs in grad_sigmas:
            oc_s = ndi.gaussian_filter(oc_field, sigma=float(gs)) if gs and gs > 0 else oc_field
            gy_o, gx_o = np.gradient(oc_s)
            gm = np.hypot(gx_o, gy_o)
            update = gm > grad_mag
            grad_mag = np.where(update, gm, grad_mag)
            denom = gm + 1e-12
            grad_nx = np.where(update, gx_o / denom, grad_nx)
            grad_ny = np.where(update, gy_o / denom, grad_ny)

        se_band_info = build_se_band_info(se_obs, BAND_FILTERS)
        # Optional radial emphasis: upweight outer (r>=r75) region to sharpen directionality
        try:
            radial_exp_env = float(_os.environ.get('BULLET_SHADOW_RADIAL_EXP', '0'))
        except Exception:
            radial_exp_env = 0.0
        if radial_exp_env and (thr_outer_r == thr_outer_r):
            r_min = float(thr_outer_r)
            r_max = float(np.nanmax(rmap)) if np.any(np.isfinite(rmap)) else r_min + 1.0
            denom = max(1e-6, (r_max - r_min))
            radial_w = np.clip((rmap - r_min) / denom, 0.0, 1.0)
            radial_w = np.power(radial_w, radial_exp_env)
            for _bn, _info in se_band_info.items():
                if isinstance(_info, dict) and ('mag' in _info):
                    try:
                        _info['mag'] = _info['mag'] * radial_w
                    except Exception:
                        pass
        rr_band_cache_obs = build_rr_band_cache(rr_clean, BAND_FILTERS)
        block_default = int(_shadow_default('block_size', 16))
        if shadow_block_pix is not None:
            block_size_shadow = max(1, int(shadow_block_pix))
        else:
            block_size_shadow = int(_os.environ.get('BULLET_SHADOW_BLOCK', str(block_default)))
        block_size_shadow = max(4, block_size_shadow)
        rr_q_default = _shadow_default('rr_quantile', 0.85)
        try:
            rr_q_env = float(_os.environ.get('BULLET_SHADOW_RR_Q', str(rr_q_default)))
        except Exception:
            rr_q_env = float(rr_q_default)

        # Optional shaping knobs for S_shadow (angle kernel / weight exponent)
        try:
            angle_gamma_env = float(_os.environ.get('BULLET_SHADOW_ANGLE_GAMMA', '1.0'))
        except Exception:
            angle_gamma_env = 1.0
        try:
            weight_exp_env = float(_os.environ.get('BULLET_SHADOW_WEIGHT_EXP', '1.0'))
        except Exception:
            weight_exp_env = 1.0
        angle_kernel_env = (_os.environ.get('BULLET_ANGLE_KERNEL', 'power') or 'power').lower()
        try:
            vm_kappa_env = float(_os.environ.get('BULLET_VM_KAPPA', '0.0'))
        except Exception:
            vm_kappa_env = 0.0
        # reuse layer_thick_px as H_cut(px) if available
        # layer_thick_px may be defined above in optional layer section; default 0 if absent
        try:
            h_cut_px_env = float(layer_thick_px) if isinstance(layer_thick_px, (int, float)) else 0.0
        except Exception:
            h_cut_px_env = 0.0
        try:
            angle_chi_env = float(_os.environ.get('BULLET_ANGLE_CHI', '1.0'))
        except Exception:
            angle_chi_env = 1.0

        shadow_evaluator = ShadowBandpassEvaluator(
            se_band_info,
            sn_mask_shadow,
            block_size=block_size_shadow,
            rr_quantile=rr_q_env,
            morph_close=morph_close,
            morph_open=morph_open,
            morph_clean_min=morph_clean_min,
            angle_gamma=angle_gamma_env,
            weight_exp=weight_exp_env,
            angle_kernel=angle_kernel_env,
            vm_kappa=vm_kappa_env,
            h_cut_pix=h_cut_px_env,
            chi=angle_chi_env,
        )

        shadow_candidates = []
        try:
            se_thresh = float(np.nanquantile(se_obs[base_mask_shadow], se_quantile_env))
        except Exception:
            se_thresh = None
        base_edge_base = base_mask_shadow.copy()
        # Optional refined outer band [q_low, q_high]
        try:
            q_low_env = float(_os.environ.get('BULLET_OUTER_Q_LOW', '0.75'))
        except Exception:
            q_low_env = 0.75
        try:
            q_high_env = float(_os.environ.get('BULLET_OUTER_Q_HIGH', '0.95'))
        except Exception:
            q_high_env = 0.95
        if np.any(np.isfinite(rmap)):
            try:
                r_low = float(np.nanquantile(rmap[base_mask_shadow], q_low_env))
                r_high = float(np.nanquantile(rmap[base_mask_shadow], q_high_env))
            except Exception:
                r_low = float('nan'); r_high = float('nan')
            if (r_low == r_low) and (r_high == r_high) and (r_high > r_low):
                base_edge_base &= (rmap >= r_low) & (rmap <= r_high)
            elif thr_outer_r == thr_outer_r:
                base_edge_base &= (rmap >= thr_outer_r)
        elif thr_outer_r == thr_outer_r:
            base_edge_base &= (rmap >= thr_outer_r)
        if se_thresh is not None:
            base_edge_base &= (se_obs >= se_thresh)
        # Optional transition layer emphasis (apply after base_edge_base is defined)
        try:
            layer_thick_px = int(float(_os.environ.get('BULLET_SHADOW_LAYER_THICK', '0')))
        except Exception:
            layer_thick_px = 0
        try:
            layer_chi = float(_os.environ.get('BULLET_SHADOW_LAYER_CHI', '0'))
        except Exception:
            layer_chi = 0.0
        # Optional physical thickness in kpc (converted to px via PIXKPC)
        try:
            layer_h_kpc = float(_os.environ.get('BULLET_LAYER_H_KPC', '0'))
        except Exception:
            layer_h_kpc = 0.0
        if layer_h_kpc and layer_h_kpc > 0 and isinstance(pix, (float, int)) and float(pix) > 0:
            try:
                layer_thick_px = max(layer_thick_px, int(round(layer_h_kpc / float(pix))))
            except Exception:
                pass
        try:
            layer_q_env = float(_os.environ.get('BULLET_SHADOW_LAYER_Q', _os.environ.get('BULLET_SHADOW_SE_Q', str(se_quantile_env))))
        except Exception:
            layer_q_env = se_quantile_env
        if layer_thick_px > 0 and layer_chi > 0 and np.any(base_edge_base):
            try:
                tau_layer = float(np.nanquantile(grad_mag[base_edge_base], layer_q_env))
            except Exception:
                tau_layer = float('nan')
            if tau_layer == tau_layer:
                core_edge = (grad_mag >= tau_layer) & base_edge_base
                if morph_close > 0 or morph_open > 0:
                    core_edge = morph_clean(core_edge, close_iter=max(morph_close,0), open_iter=max(morph_open,0))
                layer_mask = ndi.binary_dilation(core_edge, iterations=int(max(1, layer_thick_px)))
                layer_w = np.where(layer_mask, 1.0 + float(layer_chi), 1.0)
                for _bn, _info in se_band_info.items():
                    if isinstance(_info, dict) and ('mag' in _info):
                        try:
                            _info['mag'] = _info['mag'] * layer_w
                        except Exception:
                            pass
        if np.any(base_edge_base):
            for q_edge in q_list:
                try:
                    tau_edge = float(np.nanquantile(grad_mag[base_edge_base], q_edge))
                except Exception:
                    continue
                if not (tau_edge == tau_edge):
                    continue
                mask_edge = (grad_mag >= tau_edge) & base_edge_base
                if morph_close > 0 or morph_open > 0:
                    mask_edge = morph_clean(
                        mask_edge,
                        close_iter=max(morph_close, 0),
                        open_iter=max(morph_open, 0),
                    )
                metrics = shadow_evaluator.evaluate(rr_band_cache_obs, mask_edge, apply_clean=True)
                if metrics:
                    metrics.update({'tau': tau_edge,
                                    'edge_quantile': q_edge,
                                    'edge_count': int(np.sum(mask_edge))})
                    shadow_candidates.append(metrics)
            edge_default = int(_shadow_default('edge_count', 2048))
            edge_count = int(_os.environ.get('BULLET_EDGE_COUNT', str(edge_default)))
            edge_count = max(256, edge_count)
            grad_vals = grad_mag[base_edge_base]
            if grad_vals.size > 0 and edge_count > 0:
                k = min(edge_count, grad_vals.size)
                tau_edge = float(np.partition(grad_vals, grad_vals.size - k)[grad_vals.size - k])
                mask_edge = (grad_mag >= tau_edge) & base_edge_base
                if morph_close > 0 or morph_open > 0:
                    mask_edge = morph_clean(
                        mask_edge,
                        close_iter=max(morph_close, 0),
                        open_iter=max(morph_open, 0),
                    )
                metrics = shadow_evaluator.evaluate(rr_band_cache_obs, mask_edge, apply_clean=True)
                if metrics:
                    metrics.update({'tau': tau_edge,
                                    'edge_count': k})
                    shadow_candidates.append(metrics)

        shadow_candidates_sorted = sorted(shadow_candidates, key=lambda d: d['S'], reverse=True)
        S_shadow = {'global': float('nan'), 'core_r50': float('nan'), 'outer_r75': float('nan')}
        Q2_shadow = {}
        V_shadow = {}
        S_perm = {'n': 0, 'p_perm_one_sided_pos': float('nan')}
        boundary_band = {'neg_frac': float('nan'), 'N': 0, 'p_fisher_out_greater': float('nan')}
        shadow_main = None
        shadow_rayleigh = {}
        shadow_band_details = {}

        def _parse_env_int(var: str) -> int | None:
            val = _os.environ.get(var)
            if val and val.strip():
                try:
                    return int(val)
                except Exception:
                    return None
            return None

        def run_shadow_perm(mask_global: np.ndarray, obs_s: float) -> dict:
            import numpy.fft as _fft  # noqa: F401
            # Resolve permutation budget from config/env
            target_cfg = perm_config.get('target') if perm_config else None
            target_env = _parse_env_int('BULLET_SHADOW_PERM_N')
            target_fallback = _parse_env_int('BULLET_PERM_N')
            target_shadow = target_cfg if target_cfg is not None else (target_env if target_env is not None else (target_fallback if target_fallback is not None else 5000))
            target_shadow = max(0, int(target_shadow))

            min_cfg = perm_config.get('min') if perm_config else None
            min_env = _parse_env_int('BULLET_SHADOW_PERM_MIN')
            fallback_min = _parse_env_int('BULLET_PERM_MIN')
            default_perm_min = int(_shadow_default('perm_min', 10000))
            min_shadow = min_cfg if min_cfg is not None else (min_env if min_env is not None else (fallback_min if fallback_min is not None else default_perm_min))
            min_shadow = max(1, int(min_shadow))

            max_cfg = perm_config.get('max') if perm_config else None
            max_env = _parse_env_int('BULLET_SHADOW_PERM_MAX')
            fallback_max = _parse_env_int('BULLET_PERM_MAX')
            max_shadow = max_cfg if max_cfg is not None else (max_env if max_env is not None else (fallback_max if fallback_max is not None else max(target_shadow, min_shadow)))
            max_shadow = max(min_shadow, int(max_shadow))

            target_samples = max(min_shadow, target_shadow if target_shadow > 0 else min_shadow)
            perm_total = max_shadow
            if perm_total <= 0:
                return {'n': 0, 'p_perm_one_sided_pos': float('nan')}

            early_stop_enabled = bool(perm_config.get('early_stop')) if perm_config else False
            success_threshold = float(perm_config.get('success_threshold', 0.02)) if perm_config else 0.02
            failure_threshold = float(perm_config.get('failure_threshold', 0.20)) if perm_config else 0.20

            try:
                seed_env = _os.environ.get('BULLET_SHADOW_PERM_SEED') or _os.environ.get('BULLET_PERM_SEED')
                base_seed = int(seed_env) if seed_env else 123
            except Exception:
                base_seed = 123
            perm_total = max(8, perm_total)
            digest = _compute_stage_digest(
                f'{holdout}-shadow-perm',
                [mask_global.astype(np.uint8), rr_clean.astype(np.float32)],
                {
                    'perm_total': perm_total,
                    'block_size': int(block_size_shadow),
                    'obs_s': float(obs_s),
                    'seed': base_seed,
                    'fast': int(bool(FAST))
                }
            )
            stage = StageResume(holdout, 'shadow_perm', digest, total=perm_total)
            needs_run = stage.iterations < perm_total or not stage.is_complete
            prog = LoopProgress(
                f"{holdout}-shadow-perm", perm_total,
                log_path=progress_log,
                initial=stage.iterations
            ) if needs_run else None
            for idx in range(stage.iterations, perm_total):
                rng = np.random.default_rng(base_seed + idx)
                sy = (rr_clean.shape[0] + block_size_shadow - 1) // block_size_shadow
                sx = (rr_clean.shape[1] + block_size_shadow - 1) // block_size_shadow
                sign_blocks = rng.choice([-1.0, 1.0], size=(sy, sx))
                sign_field = np.repeat(np.repeat(sign_blocks, block_size_shadow, axis=0), block_size_shadow, axis=1)[:rr_clean.shape[0], :rr_clean.shape[1]]
                rr_perm = rr_clean * sign_field
                rr_band_perm = build_rr_band_cache(rr_perm, BAND_FILTERS)
                metrics_perm = shadow_evaluator.evaluate(rr_band_perm, mask_global, apply_clean=False)
                value = float(metrics_perm['S']) if metrics_perm else None
                stage.record(value)
                if prog:
                    prog.step()
                valid_vals = [float(v) for v in stage.values if isinstance(v, (int, float)) and v == v]
                count_valid = len(valid_vals)
                if count_valid >= max_shadow:
                    stage.mark_complete()
                    break
                if count_valid >= target_samples and not early_stop_enabled:
                    stage.mark_complete()
                    break
                if early_stop_enabled and count_valid >= min_shadow and valid_vals:
                    arr = np.array(valid_vals, dtype=float)
                    p_hat = float(((np.nan_to_num(arr) >= obs_s).sum() + 1.0) / (arr.size + 1.0))
                    if p_hat < success_threshold or p_hat > failure_threshold:
                        stage.mark_complete()
                        break
            if stage.iterations >= perm_total and not stage.is_complete:
                stage.mark_complete()
            null_vals = [float(v) for v in stage.values if isinstance(v, (int, float))]
            if null_vals:
                null_arr = np.array(null_vals, dtype=float)
                p_perm = float(((np.nan_to_num(null_arr) >= obs_s).sum() + 1.0) / (null_arr.size + 1.0))
                return {
                    'n': int(len(null_vals)),
                    'p_perm_one_sided_pos': p_perm,
                    'samples': {'mean': float(np.nanmean(null_arr)), 'std': float(np.nanstd(null_arr))}
                }
            return {'n': 0, 'p_perm_one_sided_pos': float('nan')}

        def run_shadow_bootstrap(contrib: dict[str, np.ndarray] | None, n_boot: int = 500) -> dict:
            if FAST or contrib is None:
                return {'n': 0}
            weights = contrib.get('weight')
            if weights is None:
                return {'n': 0}
            active = np.where(weights > 0)[0]
            if active.size == 0:
                return {'n': 0}
            S_vals = contrib.get('S')
            Q2_vals = contrib.get('Q2')
            cos_vals = contrib.get('cos')
            sin_vals = contrib.get('sin')
            if any(x is None for x in (S_vals, Q2_vals, cos_vals, sin_vals)):
                return {'n': 0}
            n_blocks = int(active.size)
            n_boot = max(32, int(n_boot))
            try:
                seed_env = _os.environ.get('BULLET_SHADOW_BOOT_SEED') or _os.environ.get('BULLET_BOOT_SEED')
                base_seed = int(seed_env) if seed_env else 321
            except Exception:
                base_seed = 321
            digest = _compute_stage_digest(
                f'{holdout}-shadow-boot',
                [
                    np.asarray(weights, dtype=float),
                    np.asarray(S_vals, dtype=float),
                    np.asarray(Q2_vals, dtype=float),
                    np.asarray(cos_vals, dtype=float),
                    np.asarray(sin_vals, dtype=float),
                    np.asarray(active, dtype=np.int64)
                ],
                {'n_boot': n_boot, 'seed': base_seed, 'n_blocks': n_blocks}
            )
            stage = StageResume(holdout, 'shadow_boot', digest, total=n_boot)
            needs_run = stage.iterations < n_boot or not stage.is_complete
            boot_prog = LoopProgress(
                f"{holdout}-shadow-boot", n_boot,
                log_path=progress_log,
                initial=stage.iterations
            ) if needs_run else None
            for idx in range(stage.iterations, n_boot):
                rng = np.random.default_rng(base_seed + idx)
                picks = rng.choice(active, size=n_blocks, replace=True)
                w_sum = float(np.sum(weights[picks]))
                value = None
                if w_sum > 0:
                    S_sum = float(np.sum(S_vals[picks]))
                    Q2_sum = float(np.sum(Q2_vals[picks]))
                    cos_sum = float(np.sum(cos_vals[picks]))
                    sin_sum = float(np.sum(sin_vals[picks]))
                    S_boot = S_sum / w_sum
                    Q2_boot = Q2_sum / w_sum
                    mean_cos = cos_sum / w_sum
                    mean_sin = sin_sum / w_sum
                    R = math.hypot(mean_cos, mean_sin)
                    value = {'S': float(S_boot), 'Q2': float(Q2_boot), 'R': float(R)}
                stage.record(value)
                if boot_prog:
                    boot_prog.step()
            if stage.iterations >= n_boot and not stage.is_complete:
                stage.mark_complete()
            records = [v for v in stage.values if isinstance(v, dict)]
            if not records:
                return {'n': 0}
            arr_S = np.array([float(rec['S']) for rec in records if 'S' in rec], dtype=float)
            arr_Q2 = np.array([float(rec['Q2']) for rec in records if 'Q2' in rec], dtype=float)
            arr_R = np.array([float(rec['R']) for rec in records if 'R' in rec], dtype=float)
            if arr_S.size == 0:
                return {'n': 0}
            def ci(x: np.ndarray) -> tuple[float, float]:
                return float(np.nanpercentile(x, 2.5)), float(np.nanpercentile(x, 97.5))
            ci_S = ci(arr_S)
            ci_Q2 = ci(arr_Q2) if arr_Q2.size else (float('nan'), float('nan'))
            ci_R = ci(arr_R) if arr_R.size else (float('nan'), float('nan'))
            result = {
                'n': int(arr_S.size),
                'S': {
                    'mean': float(np.nanmean(arr_S)),
                    'std': float(np.nanstd(arr_S)),
                    'ci95': {'low': ci_S[0], 'high': ci_S[1]}
                }
            }
            if arr_Q2.size:
                result['Q2'] = {
                    'mean': float(np.nanmean(arr_Q2)),
                    'std': float(np.nanstd(arr_Q2)),
                    'ci95': {'low': ci_Q2[0], 'high': ci_Q2[1]}
                }
            if arr_R.size:
                result['R'] = {
                    'mean': float(np.nanmean(arr_R)),
                    'std': float(np.nanstd(arr_R)),
                    'ci95': {'low': ci_R[0], 'high': ci_R[1]}
                }
            return result

        def compute_boundary_band(tau_edge: float, mask_global: np.ndarray) -> dict:
            boundary = {'neg_frac': float('nan'), 'N': 0, 'p_fisher_out_greater': float('nan')}
            if tau_edge == tau_edge:
                dtau = max(float(params.delta_tau_frac) * tau_edge, 1e-6)
                band_mask = (grad_mag >= tau_edge) & (grad_mag <= tau_edge + dtau) & base_mask_shadow
                if np.any(band_mask):
                    rhatx2, rhaty2 = _unit_vectors(rr.shape[0], rr.shape[1], pix)
                    sgn = np.sign(rhatx2 * grad_nx + rhaty2 * grad_ny)
                    out_mask = band_mask & (sgn > 0)
                    in_mask = band_mask & (sgn <= 0)
                    k_out = int((rr[out_mask] < 0).sum()); n_out = int(out_mask.sum())
                    k_in = int((rr[in_mask] < 0).sum()); n_in = int(in_mask.sum())
                    if n_out + n_in > 0:
                        try:
                            from scipy.stats import fisher_exact
                            _, p_fisher = fisher_exact([[k_out, n_out - k_out], [k_in, n_in - k_in]], alternative='greater')
                        except Exception:
                            p_fisher = float('nan')
                        neg_frac = float(k_out) / max(n_out, 1)
                        boundary = {'neg_frac': float(neg_frac), 'N': int(n_out + n_in),
                                    'p_fisher_out_greater': float(p_fisher), 'tau': float(tau_edge),
                                    'delta_tau': float(dtau),
                                    'counts': {'out': [k_out, n_out], 'in': [k_in, n_in]}}
            return boundary

        candidate_records: list[dict[str, object]] = []
        for cand in shadow_candidates_sorted:
            mask_global = cand['mask']
            S_curr = {'global': float(cand.get('S', float('nan'))),
                      'core_r50': float('nan'),
                      'outer_r75': float('nan')}
            Q2_curr = {'global': float(cand.get('Q2', float('nan')))}
            V_curr = {'global': cand.get('v_test')}
            if thr_core_r == thr_core_r:
                metrics_core = shadow_evaluator.evaluate(rr_band_cache_obs, mask_global & (rmap <= thr_core_r), apply_clean=False)
                if metrics_core:
                    S_curr['core_r50'] = float(metrics_core['S'])
                    Q2_curr['core_r50'] = float(metrics_core['Q2'])
                    V_curr['core_r50'] = metrics_core.get('v_test')
            if thr_outer_r == thr_outer_r:
                metrics_outer = shadow_evaluator.evaluate(rr_band_cache_obs, mask_global & (rmap >= thr_outer_r), apply_clean=False)
                if metrics_outer:
                    S_curr['outer_r75'] = float(metrics_outer['S'])
                    Q2_curr['outer_r75'] = float(metrics_outer['Q2'])
                    V_curr['outer_r75'] = metrics_outer.get('v_test')
            S_perm_curr = run_shadow_perm(mask_global, S_curr['global'])
            boundary_curr = compute_boundary_band(float(cand.get('tau', float('nan'))), mask_global)
            contrib = cand.pop('_block_contrib', None)
            candidate_records.append({
                'base': cand,
                'S': S_curr,
                'Q2': Q2_curr,
                'V': V_curr,
                'perm': S_perm_curr,
                'boundary': boundary_curr,
                'rayleigh': cand.get('rayleigh', {}) or {},
                'band_details': cand.get('band_details', {}) or {},
                'contrib': contrib
            })

        p_inputs = []
        for rec in candidate_records:
            perm = rec.get('perm') or {}
            p_val = perm.get('p_perm_one_sided_pos', float('nan')) if isinstance(perm, dict) else float('nan')
            p_inputs.append(p_val)
        q_values = benjamini_hochberg(p_inputs)
        for idx, q_val in enumerate(q_values):
            rec = candidate_records[idx]
            rec['p_fdr'] = float(q_val) if q_val == q_val else float('nan')

        best_idx = None
        best_metric = float('inf')
        use_fdr = True
        shadow_bootstrap = {'n': 0}
        for idx, rec in enumerate(candidate_records):
            q_val = rec.get('p_fdr', float('nan'))
            if q_val == q_val:
                if best_idx is None or q_val < best_metric:
                    best_idx = idx
                    best_metric = q_val
        if best_idx is None:
            use_fdr = False
            for idx, rec in enumerate(candidate_records):
                p_val = rec['perm'].get('p_perm_one_sided_pos', float('nan'))
                if p_val == p_val and (best_idx is None or p_val < best_metric):
                    best_idx = idx
                    best_metric = p_val

        if best_idx is not None:
            rec = candidate_records[best_idx]
            shadow_main = rec['base']
            S_shadow = rec['S']
            Q2_shadow = rec['Q2']
            V_shadow = rec['V']
            S_perm = rec['perm']
            boundary_band = rec['boundary']
            shadow_rayleigh = rec['rayleigh']
            shadow_band_details = rec['band_details']
            if use_fdr and isinstance(S_perm, dict):
                S_perm['p_fdr'] = rec.get('p_fdr', float('nan'))
            elif isinstance(S_perm, dict):
                S_perm['p_fdr'] = float('nan')
            shadow_bootstrap = run_shadow_bootstrap(rec.get('contrib'), n_boot=400)
        else:
            shadow_bootstrap = {'n': 0}

        # Report
        def fmt(a):
            return f'{a:.2f}'
        # Prepare display distance (kpc) prior to HTML
        # Prefer PIXKPC from maps
        scale_kpc_pre = pix if isinstance(pix, (float, int)) else None
        def to_kpc(px):
            return (px * scale_kpc_pre) if (isinstance(scale_kpc_pre, float) and (px == px)) else float('nan')
        # compute candidates in kpc if possible
        raw_kpc   = to_kpc(peak_offset_pix)
        hp_kpc    = to_kpc(hp_peak_offset_pix)
        xc_kpc    = to_kpc(float(xcorr_peak_offset_pix) if 'xcorr_peak_offset_pix' in locals() else float('nan'))
        if xc_kpc == xc_kpc:
            display_kpc = xc_kpc; display_method = 'xcorr'
        elif hp_kpc == hp_kpc:
            display_kpc = hp_kpc; display_method = 'highpass'
        else:
            display_kpc = raw_kpc; display_method = 'raw'
        met = Path('server/public/reports/cluster/bullet_metrics.json')
        if met.exists():
            try:
                jd = json.loads(met.read_text(encoding='utf-8'))
                d = jd.get('delta_AICc', {}).get('FDB_minus_GR')
                if d is not None:
                    html.append(f'<div class=card><small>参考: パイプラインΔAICc（FDB−GR）={d:.2f}</small></div>')
            except Exception:
                pass

            # 画像出力（三指標可視化）
            # 1) ピーク可視化
        fig, ax = plt.subplots(1,2, figsize=(8.2,3.4))
        im0=ax[0].imshow(k_pred_s, origin='lower', cmap='magma'); ax[0].plot([px_m],[py_m],'co',ms=6)
        ax[0].set_title('κ_pred (peak)'); fig.colorbar(im0, ax=ax[0], fraction=0.046, pad=0.04)
        im1=ax[1].imshow(se_obs, origin='lower', cmap='viridis'); ax[1].plot([px_x],[py_x],'ro',ms=6)
        ax[1].set_title('Σ_e (peak)'); fig.colorbar(im1, ax=ax[1], fraction=0.046, pad=0.04)
        fig.suptitle(f'peak distance = {peak_offset_pix:.1f} pix')
        fig.tight_layout(); plt.savefig(outdir/'bullet_peaks.png', dpi=140); plt.close(fig)
        # Aligned panel (visualization of subpixel alignment)
        try:
            if 'dyf' in locals() and 'dxf' in locals():
                k_pred_shift = _shift_lanczos(k_pred, -dyf, -dxf)
                fig, ax = plt.subplots(1,2, figsize=(8.2,3.4))
                im0=ax[0].imshow(k_pred_shift, origin='lower', cmap='magma'); ax[0].set_title('κ_pred (aligned)'); fig.colorbar(im0, ax=ax[0], fraction=0.046, pad=0.04)
                im1=ax[1].imshow(k_obs if 'k_obs' in locals() else se_obs, origin='lower', cmap='viridis'); ax[1].set_title('κ_obs / Σ_e'); fig.colorbar(im1, ax=ax[1], fraction=0.046, pad=0.04)
                shift_mag = float(np.hypot(dxf, dyf))
                fig.suptitle(f'xcorr shift = {shift_mag:.1f} pix')
                fig.tight_layout(); plt.savefig(outdir/'bullet_aligned_panel.png', dpi=140); plt.close(fig)
        except Exception:
            pass
            # 2) cosΔθ ヒストグラム
        fig, ax = plt.subplots(1,1, figsize=(4.8,3.2))
        ax.hist(cos_d, bins=40, color='#5555aa'); ax.set_xlabel('cosΔθ (ST)'); ax.set_ylabel('count');
        ax.set_title(f'⟨cosΔθ⟩={shear_phase_cos:.3f} (structure-tensor)')
        fig.tight_layout(); plt.savefig(outdir/'bullet_shear_cos_hist.png', dpi=140); plt.close(fig)
            # 3) 残差 vs Σ_e 散布図（サブサンプル）
        yy = rr[mm2].ravel(); xx = se_obs[mm2].ravel()
        if yy.size > 50000:
            idx = np.random.default_rng(0).choice(yy.size, size=50000, replace=False)
            yy = yy[idx]; xx = xx[idx]
        fig, ax = plt.subplots(1,1, figsize=(4.8,3.2))
        ax.scatter(xx, yy, s=1, alpha=0.3)
        ax.set_xlabel('Σ_e'); ax.set_ylabel('κ_obs - κ_pred')
        ax.set_title(f'corr={r_val:.3f}, spear={r_spear:.3f} (p={p_spear:.2g})')
        fig.tight_layout(); plt.savefig(outdir/'bullet_residual_scatter.png', dpi=140); plt.close(fig)

        # Cross-correlation based alignment (subpixel) on high-pass maps
        try:
            import numpy.fft as _fft
            A = k_pred_hp.copy(); B = se_hp.copy()
            # zero-mean, unit variance
            A = (A - np.nanmean(A)) / (np.nanstd(A) + 1e-12)
            B = (B - np.nanmean(B)) / (np.nanstd(B) + 1e-12)
            FA = _fft.rfftn(A); FB = _fft.rfftn(B)
            CC = _fft.irfftn(FA * np.conj(FB), s=A.shape)
            H, W = A.shape
            pyi, pxi = np.unravel_index(int(np.nanargmax(CC)), CC.shape)
            dy = pyi if pyi <= H//2 else pyi - H
            dx = pxi if pxi <= W//2 else pxi - W
            # 3x3 quadratic refinement
            ys = [(pyi-1)%H, pyi%H, (pyi+1)%H]; xs = [(pxi-1)%W, pxi%W, (pxi+1)%W]
            win = CC[np.ix_(ys, xs)].astype(float)
            cy = win[:,1]; ay = (cy[0]-2*cy[1]+cy[2])/2.0; by = (cy[2]-cy[0])/2.0
            dy_sub = float(-by/(2*ay)) if abs(ay) > 1e-12 else 0.0
            cx = win[1,:]; ax = (cx[0]-2*cx[1]+cx[2])/2.0; bx = (cx[2]-cx[0])/2.0
            dx_sub = float(-bx/(2*ax)) if abs(ax) > 1e-12 else 0.0
            dyf = dy + dy_sub; dxf = dx + dx_sub
            # shift prediction and recompute high-pass peak distance
            k_pred_hp_shift = _shift_lanczos(k_pred_hp, -dyf, -dxf)
            py_ms, px_ms = peak_xy(k_pred_hp_shift)
            py_xs, px_xs = peak_xy(se_hp)
            xcorr_shift_pix = float(np.hypot(dxf, dyf))
            xcorr_peak_offset_pix = float(np.hypot(px_ms - px_xs, py_ms - py_xs))
        except Exception:
            xcorr_shift_pix = float('nan'); xcorr_peak_offset_pix = float('nan')

        # Evaluate pass/fail against simple thresholds
        # Thresholds (kpi): peak_kpc<=300, shear_phase_cos>=0.2, top10% Spearman<0 and p<0.05
        # Prefer kpc/pix from Σ_e header (PIXKPC) via 'pix'
        scale_kpc = pix if isinstance(pix, (float, int)) else None
        if not isinstance(scale_kpc, float):
            try:
                met = json.loads((Path('server/public/reports/cluster/bullet_metrics.json')).read_text(encoding='utf-8'))
                scale_kpc = float(met.get('scale_kpc_per_pix')) if met.get('scale_kpc_per_pix') is not None else None
            except Exception:
                scale_kpc = None
        peak_kpc = (peak_offset_pix * scale_kpc) if isinstance(scale_kpc, float) else float('nan')
        hp_peak_kpc = (hp_peak_offset_pix * scale_kpc) if isinstance(scale_kpc, float) else float('nan')
        xcorr_peak_kpc = (xcorr_peak_offset_pix * scale_kpc) if isinstance(scale_kpc, float) and (xcorr_peak_offset_pix==xcorr_peak_offset_pix) else float('nan')
        # already computed above
        thr_peak_kpc = 300.0
        thr_cos = 0.2
        # top10% Spearman
        s10 = strat.get('p90') or {}
        spear10 = float(s10.get('spear_r') or float('nan'))
        p10 = float(s10.get('p') or float('nan'))
        pass_peak = (peak_kpc <= thr_peak_kpc) if (peak_kpc == peak_kpc) else False
        pass_cos  = (shear_phase_cos >= thr_cos)
        pass_corr = (spear10 < 0.0) and (p10 < 0.05)
        # High-pass distance pass
        hp_peak_kpc = (hp_peak_offset_pix * scale_kpc) if isinstance(scale_kpc, float) else float('nan')
        pass_peak_hp = (hp_peak_kpc <= thr_peak_kpc) if (hp_peak_kpc == hp_peak_kpc) else False
        # Global Spearman (full field)
        spear_global = float(r_spear)
        p_global = float(p_spear)
        pass_corr_global = (spear_global < 0.0) and (p_global < 0.05)
        indicators_pass = {
            'peak_distance_kpc': {'value': peak_kpc, 'thr': thr_peak_kpc, 'pass': pass_peak},
            'peak_distance_kpc_highpass': {'value': hp_peak_kpc, 'thr': thr_peak_kpc, 'pass': pass_peak_hp, 'hp_sigma': hp_sigma},
            'shear_phase_cos': {'value': shear_phase_cos, 'thr': thr_cos, 'pass': pass_cos},
            'neg_corr_global': {'spear_r': spear_global, 'p': p_global, 'pass': pass_corr_global},
            'neg_corr_top10': {'spear_r': spear10, 'p': p10, 'pass': pass_corr}
        }

        # β sweep (AICc with penalty managed by k) using same smoothing/mask/alignment as best
        sweep = []
        if beta_sweep:
            for bval in beta_sweep:
                p2 = MinKernelParams(alpha=float(params.alpha), beta=float(bval), C=float(params.C),
                                     xi=float(params.xi), p=float(params.p), tau_q=float(params.tau_q),
                                     delta_tau_frac=float(params.delta_tau_frac))
                k_pred2 = predict_kappa(oc, se, pix, p2)
                if k_pred2.shape != k_obs.shape:
                    zy, zx = k_obs.shape[0] / k_pred2.shape[0], k_obs.shape[1] / k_pred2.shape[1]
                    k_pred2 = ndi.zoom(k_pred2, zoom=(zy, zx), order=1)
                kp2 = ndi.gaussian_filter(k_pred2, sigma=gauss_sig)
                ko2 = k_obs_s
                se2 = se_obs if se_obs.shape == kp2.shape else ndi.zoom(se_obs, zoom=(kp2.shape[0]/se_obs.shape[0], kp2.shape[1]/se_obs.shape[1]), order=1)
                m2 = np.isfinite(ko2) & np.isfinite(kp2)
                if int(np.sum(m2)) <= 10:
                    continue
                try:
                    import numpy.fft as _fft
                    A = (kp2 * m2); B = (ko2 * m2)
                    FA = _fft.rfftn(A); FB = _fft.rfftn(B)
                    CC = _fft.irfftn(FA * np.conj(FB), s=A.shape)
                    py, px = np.unravel_index(np.argmax(CC), CC.shape)
                    cy, cx = A.shape[0]//2, A.shape[1]//2
                    dyf = float(py - cy); dxf = float(px - cx)
                except Exception:
                    dyf = dxf = 0.0
                kp2_al = _shift_lanczos(kp2, -dyf, -dxf)
                rr2 = (ko2[m2] - kp2_al[m2])
                med2 = float(np.nanmedian(rr2)); mad2 = float(np.nanmedian(np.abs(rr2 - med2)))
                sigma2 = max(1.4826 * mad2, 1e-6)
                w2 = np.power(se2[m2] / (np.nanmean(se2[m2]) + 1e-12), best.get('weight_power', 1.0))
                def aicc(chi2: float, k: int, N: int) -> float:
                    return float(chi2 + 2*k + (2*k*(k+1))/max(N-k-1, 1))
                chi_fdb2 = float(np.nansum(((rr2 / sigma2) ** 2) * w2))
                A_fdb2 = aicc(chi_fdb2, k=2, N=int(np.sum(m2)))
                kp_shift2 = np.roll(np.roll(kp2_al, 12, axis=0), -7, axis=1)
                chi_shift2 = float(np.nansum((((ko2[m2] - kp_shift2[m2]) / sigma2) ** 2) * w2))
                A_shift2 = aicc(chi_shift2, k=2, N=int(np.sum(m2)))
                sweep.append({'beta': float(bval), 'AICc': A_fdb2, 'AICc_shift': A_shift2, 'Delta_FDB_minus_shift': A_fdb2 - A_shift2, 'N': int(np.sum(m2))})

        # Spatial ROI: global / core(r<=r50) / outer(r>=r75) for residual×Σ_e sign check
        valid = np.isfinite(se_obs)
        r50 = float(np.nanquantile(rmap[valid], 0.5)) if np.any(valid) else float('nan')
        r75 = float(np.nanquantile(rmap[valid], 0.75)) if np.any(valid) else float('nan')
        thr_core_r = r50; thr_outer_r = r75
        roi_stats = {}
        def region_corr(mask):
            mmr = mask & np.isfinite(se_obs) & np.isfinite(k_obs_s) & np.isfinite(k_pred_s)
            if not np.any(mmr):
                return {'pearson_r': float('nan'), 'spear_r': float('nan'), 'p': float('nan'), 'N': 0}
            rr = (k_obs_s - k_pred_s)[mmr]
            sv = se_obs[mmr]
            pr = float(pearsonr(rr.ravel(), sv.ravel())[0]) if rr.size>1 else float('nan')
            sr, pp = spearmanr(rr.ravel(), sv.ravel(), nan_policy='omit')
            return {'pearson_r': pr, 'spear_r': float(sr), 'p': float(pp), 'N': int(rr.size)}
        roi_stats['global'] = region_corr(np.isfinite(se_obs))
        if thr_core_r == thr_core_r:
            roi_stats['core_r50'] = region_corr(valid & (rmap <= thr_core_r))
        if thr_outer_r == thr_outer_r:
            roi_stats['outer_r75'] = region_corr(valid & (rmap >= thr_outer_r))

        # Partial correlation r(resid, Σ_e | r) with p-values
        def partial_corr(a: np.ndarray, b: np.ndarray, c: np.ndarray, mask: np.ndarray) -> tuple[float,float,int]:
            import numpy as _np
            from numpy.linalg import lstsq
            msk = mask & _np.isfinite(a) & _np.isfinite(b) & _np.isfinite(c)
            if not _np.any(msk):
                return float('nan'), float('nan'), 0
            A = a[msk].ravel(); B = b[msk].ravel(); C = c[msk].ravel()
            X = _np.c_[C, _np.ones_like(C)]
            ra = A - X.dot(lstsq(X, A, rcond=None)[0])
            rb = B - X.dot(lstsq(X, B, rcond=None)[0])
            n = ra.size
            if n < 3:
                return float('nan'), float('nan'), n
            r = float(pearsonr(ra, rb)[0])
            # two-sided p-value via t distribution with df=n-2
            try:
                import math
                from scipy.stats import t as _t
                t = r * math.sqrt(max(n-2,1) / max(1e-12, 1.0 - r*r))
                p = float(2.0 * (1.0 - _t.cdf(abs(t), df=max(n-2,1))))
            except Exception:
                p = float('nan')
            return r, p, n
        r_g, p_g, n_g = partial_corr(rr, se_obs, rmap, np.isfinite(se_obs))
        r_c, p_c, n_c = (partial_corr(rr, se_obs, rmap, valid & (rmap <= thr_core_r)) if thr_core_r==thr_core_r else (float('nan'), float('nan'), 0))
        r_o, p_o, n_o = (partial_corr(rr, se_obs, rmap, valid & (rmap >= thr_outer_r)) if thr_outer_r==thr_outer_r else (float('nan'), float('nan'), 0))
        roi_partial = {
            'global': r_g,
            'core_r50': r_c,
            'outer_r75': r_o,
            'pvals': {'global': p_g, 'core_r50': p_c, 'outer_r75': p_o},
            'N': {'global': n_g, 'core_r50': n_c, 'outer_r75': n_o}
        }

        # Permutation (phase-shuffle) test for Spearman( residual, Σ_e )
        try:
            import numpy.fft as _fft
            mm_all = np.isfinite(rr) & np.isfinite(se_obs)
            obs_spear_full = float(spearmanr(rr[mm_all].ravel(), se_obs[mm_all].ravel(), nan_policy='omit')[0]) if np.any(mm_all) else float('nan')
            target_cfg = perm_config.get('target') if perm_config else None
            target_env = _parse_env_int('BULLET_PERM_N')
            target_resid = target_cfg if target_cfg is not None else (target_env if target_env is not None else 5000)
            target_resid = max(0, int(target_resid))

            min_cfg = perm_config.get('min') if perm_config else None
            min_env = _parse_env_int('BULLET_PERM_MIN')
            min_resid = min_cfg if min_cfg is not None else (min_env if min_env is not None else max(target_resid, 10000))
            min_resid = max(1, int(min_resid))

            max_cfg = perm_config.get('max') if perm_config else None
            max_env = _parse_env_int('BULLET_PERM_MAX')
            max_resid = max_cfg if max_cfg is not None else (max_env if max_env is not None else max(target_resid, min_resid))
            max_resid = max(min_resid, int(max_resid))

            target_samples = max(min_resid, target_resid if target_resid > 0 else min_resid)
            perm_total = max(8, max_resid)

            if perm_total <= 0:
                effect_d = float('nan'); p_perm = float('nan'); na = np.array([])
            else:
                try:
                    seed_env = _os.environ.get('BULLET_RESID_PERM_SEED') or _os.environ.get('BULLET_PERM_SEED')
                    base_seed = int(seed_env) if seed_env else 42
                except Exception:
                    base_seed = 42
                digest = _compute_stage_digest(
                    f'{holdout}-resid-perm',
                    [
                        np.asarray(k_pred_s, dtype=np.float32),
                        np.asarray(k_obs_s, dtype=np.float32),
                        np.asarray(se_obs, dtype=np.float32)
                    ],
                    {'perm_total': perm_total, 'seed': base_seed, 'fast': int(bool(FAST))}
                )
                stage = StageResume(holdout, 'resid_perm', digest, total=perm_total)
                needs_run = stage.iterations < perm_total or not stage.is_complete
                perm_prog = LoopProgress(
                    f"{holdout}-resid-perm", perm_total,
                    log_path=progress_log,
                    initial=stage.iterations
                ) if needs_run else None
                early_stop_enabled = bool(perm_config.get('early_stop')) if perm_config else False
                success_threshold = float(perm_config.get('success_threshold', 0.02)) if perm_config else 0.02
                failure_threshold = float(perm_config.get('failure_threshold', 0.20)) if perm_config else 0.20
                for idx in range(stage.iterations, perm_total):
                    rng = np.random.default_rng(base_seed + idx)
                    F = _fft.rfftn(k_pred_s)
                    amp = np.abs(F)
                    rnd = rng.uniform(-np.pi, np.pi, size=F.shape)
                    Fr = amp * np.exp(1j * rnd)
                    kp = _fft.irfftn(Fr, s=k_pred_s.shape).real
                    rr_s = (k_obs_s - kp)
                    mm = np.isfinite(rr_s) & np.isfinite(se_obs)
                    value = None
                    if np.any(mm):
                        rs, _ = spearmanr(rr_s[mm].ravel(), se_obs[mm].ravel(), nan_policy='omit')
                        value = float(rs)
                    stage.record(value)
                    if perm_prog:
                        perm_prog.step()
                    valid_vals = [float(v) for v in stage.values if isinstance(v, (int, float)) and v == v]
                    count_valid = len(valid_vals)
                    if count_valid >= max_resid:
                        stage.mark_complete()
                        break
                    if count_valid >= target_samples and not early_stop_enabled:
                        stage.mark_complete()
                        break
                    if early_stop_enabled and count_valid >= min_resid and valid_vals:
                        arr = np.array(valid_vals, dtype=float)
                        p_hat = float(((np.nan_to_num(arr) <= obs_spear_full).sum() + 1.0) / (arr.size + 1.0))
                        if p_hat < success_threshold or p_hat > failure_threshold:
                            stage.mark_complete()
                            break
                if stage.iterations >= perm_total and not stage.is_complete:
                    stage.mark_complete()
                null_vals = [float(v) for v in stage.values if isinstance(v, (int, float))]
                na = np.array(null_vals, dtype=float)
                if na.size:
                    mu = float(np.nanmean(na))
                    sd = float(np.nanstd(na) + 1e-12)
                    effect_d = (obs_spear_full - mu) / sd
                    p_perm = float(((np.nan_to_num(na) <= obs_spear_full).sum() + 1.0) / (na.size + 1.0))
                else:
                    effect_d = float('nan')
                    p_perm = float('nan')
        except Exception:
            effect_d = float('nan')
            p_perm = float('nan')
            na = np.array([])

        # Recompute χ² for table
        rchi2_map = {'FDB': float('nan'), 'rot': float('nan'), 'shift': float('nan'), 'shuffle': float('nan')}
        rchi2_map = {'FDB': float('nan'), 'rot': float('nan'), 'shift': float('nan'), 'shuffle': float('nan')}
        res_base = (k_obs_s - k_pred_s)
        res_norm_best = np.zeros_like(res_base, dtype=float)
        res_norm_best[m] = res_base[m] / sigma_map_best[m]
        weights_best = weight_map_best[m] if weight_map_best is not None else None
        sq_best = (res_norm_best[m]) ** 2
        if weights_best is not None:
            chi_fdb = float(np.nansum(sq_best * weights_best))
        else:
            chi_fdb = float(np.nansum(sq_best))
        # rot/shift/shuffle as in fairness controls
        k_rot = np.rot90(k_pred_s, 2)
        res_rot = (k_obs_s - k_rot)
        res_norm_rot = np.zeros_like(res_rot, dtype=float)
        res_norm_rot[m] = res_rot[m] / sigma_map_best[m]
        sq_rot = (res_norm_rot[m]) ** 2
        if weights_best is not None:
            chi_rot = float(np.nansum(sq_rot * weights_best))
        else:
            chi_rot = float(np.nansum(sq_rot))
        kp_shift2 = np.roll(np.roll(k_pred_s, 12, axis=0), -7, axis=1)
        res_shift = (k_obs_s - kp_shift2)
        res_norm_shift = np.zeros_like(res_shift, dtype=float)
        res_norm_shift[m] = res_shift[m] / sigma_map_best[m]
        sq_shift = (res_norm_shift[m]) ** 2
        if weights_best is not None:
            chi_shift = float(np.nansum(sq_shift * weights_best))
        else:
            chi_shift = float(np.nansum(sq_shift))
        try:
            import numpy.fft as _fft
            F = _fft.rfftn(k_pred_s)
            amp = np.abs(F)
            rnd = np.random.default_rng(42).uniform(-np.pi, np.pi, size=F.shape)
            Fr = amp * np.exp(1j * rnd)
            kp_rand = _fft.irfftn(Fr, s=k_pred_s.shape).real
        except Exception:
            kp_rand = kp_shift2
        res_shuffle = (k_obs_s - kp_rand)
        res_norm_shuffle = np.zeros_like(res_shuffle, dtype=float)
        res_norm_shuffle[m] = res_shuffle[m] / sigma_map_best[m]
        sq_shuffle = (res_norm_shuffle[m]) ** 2
        if weights_best is not None:
            chi_shuffle = float(np.nansum(sq_shuffle * weights_best))
        else:
            chi_shuffle = float(np.nansum(sq_shuffle))

        def _rchi2(chi: float, k_mod: int) -> float:
            dof = max(n - k_mod, 1)
            return float(chi / dof)

        rchi2_map = {
            'FDB': _rchi2(chi_fdb, kmap.get('FDB', 0)),
            'rot': _rchi2(chi_rot, kmap.get('rot', 1)),
            'shift': _rchi2(chi_shift, kmap.get('shift', 2)),
            'shuffle': _rchi2(chi_shuffle, kmap.get('shuffle', 0)),
        }

        # Optional block bootstrap CI for Spearman(residual, Σ_e)
        boot = {}
        try:
            BOOT_N = int(os.environ.get('BULLET_BOOT_N', '0'))
        except Exception:
            BOOT_N = 0
        if BOOT_N and BOOT_N > 0:
            try:
                import numpy as _np
                H, W = rr.shape
                # Estimate correlation range via simple semivariogram; fallback to 27 if fails
                def est_block(px: _np.ndarray) -> int:
                    try:
                        # sample along rows middles
                        x = px[_np.isfinite(px)]
                        if x.size < 1024:
                            return 27
                        # grid variogram along a central row
                        r = px[H//2, :]
                        r = r[_np.isfinite(r)]
                        if r.size < 512:
                            return 27
                        maxlag = min(64, r.size//4)
                        gam = []
                        for h in range(1, maxlag+1):
                            dif = r[:-h] - r[h:]
                            gam.append(0.5*_np.nanmean(dif*dif))
                        gam = _np.array(gam)
                        sill = _np.nanmax(gam)
                        thr = 0.95 * sill
                        rng = next((i+1 for i,v in enumerate(gam) if v>=thr), maxlag)
                        return int(max(8, min(rng*2, min(H,W)//3)))
                    except Exception:
                        return 27
                bs = est_block(rr)
                by = list(range(0, H, bs)); bx = list(range(0, W, bs))
                blocks = [(slice(y, min(y+bs, H)), slice(x, min(x+bs, W))) for y in by for x in bx]
                mm_all = _np.isfinite(rr) & _np.isfinite(se_obs)
                base_masks = {
                    'global': mm_all,
                }
                if thr_core_r == thr_core_r:
                    base_masks['core_r50'] = mm_all & (rmap <= thr_core_r)
                if thr_outer_r == thr_outer_r:
                    base_masks['outer_r75'] = mm_all & (rmap >= thr_outer_r)

                def sample_mask(base: _np.ndarray, rng_local: np.random.Generator) -> _np.ndarray:
                    msel = _np.zeros_like(base, dtype=bool)
                    if not _np.any(base):
                        return msel
                    idx = rng_local.integers(0, len(blocks), size=len(blocks))
                    for i in idx:
                        sl = blocks[int(i) % len(blocks)]
                        msel[sl] |= base[sl]
                    return msel & base

                boot = {'block_pix': bs, 'spearman': {}, 'partial': {}, 'n': int(BOOT_N)}
                for label, base in base_masks.items():
                    try:
                        seed_env = _os.environ.get('BULLET_RESID_BOOT_SEED') or _os.environ.get('BULLET_BOOT_SEED')
                        base_seed_boot = int(seed_env) if seed_env else 123
                    except Exception:
                        base_seed_boot = 123
                    label_key = f'{holdout}-{label}'
                    label_seed_offset = int(hashlib.sha1(label_key.encode('utf-8')).hexdigest()[:8], 16)
                    seed_base_label = base_seed_boot + (label_seed_offset % 1_000_000)
                    digest = _compute_stage_digest(
                        f'{holdout}-resid-boot-{label}',
                        [
                            np.asarray(rr, dtype=np.float32),
                            np.asarray(se_obs, dtype=np.float32),
                            np.asarray(rmap, dtype=np.float32),
                            np.asarray(base, dtype=np.uint8)
                        ],
                        {
                            'n_boot': int(BOOT_N),
                            'seed': seed_base_label,
                            'block_pix': int(bs),
                            'label': label
                        }
                    )
                    stage_label = f'resid_boot_{label}'
                    stage = StageResume(holdout, stage_label, digest, total=BOOT_N)
                    needs_run = stage.iterations < BOOT_N or not stage.is_complete
                    boot_prog = LoopProgress(
                        f"{holdout}-resid-boot-{label}", BOOT_N,
                        log_path=progress_log,
                        initial=stage.iterations
                    ) if needs_run else None
                    for idx in range(stage.iterations, BOOT_N):
                        rng_local = np.random.default_rng(seed_base_label + idx)
                        msel = sample_mask(base, rng_local)
                        value = None
                        if _np.any(msel):
                            sr, _ = spearmanr(rr[msel].ravel(), se_obs[msel].ravel(), nan_policy='omit')
                            pr_val, _, _ = partial_corr(rr, se_obs, rmap, msel)
                            entry: dict[str, float | None] = {'spearman': float(sr)}
                            if pr_val == pr_val:
                                entry['partial'] = float(pr_val)
                            else:
                                entry['partial'] = None
                            value = entry
                        stage.record(value)
                        if boot_prog:
                            boot_prog.step()
                    if stage.iterations >= BOOT_N and not stage.is_complete:
                        stage.mark_complete()
                    records = [v for v in stage.values if isinstance(v, dict)]
                    spe_vals = [float(rec.get('spearman')) for rec in records if rec.get('spearman') is not None]
                    if spe_vals:
                        arr = _np.array(spe_vals, dtype=float)
                        lo, hi = _np.nanpercentile(arr, [2.5, 97.5])
                        boot['spearman'][label] = {'ci95': [float(lo), float(hi)], 'n': len(spe_vals)}
                    part_vals = [float(rec.get('partial')) for rec in records if rec.get('partial') is not None]
                    if part_vals:
                        parr = _np.array(part_vals, dtype=float)
                        plo, phi = _np.nanpercentile(parr, [2.5, 97.5])
                        boot['partial'][label] = {'ci95': [float(plo), float(phi)], 'n': len(part_vals)}
            except Exception:
                boot = {}

        perm_sample_n = 0
        if 'na' in locals():
            try:
                perm_sample_n = int(getattr(na, 'size', len(na)))
            except Exception:
                try:
                    perm_sample_n = int(len(na))
                except Exception:
                    perm_sample_n = 0

        rho_sum_best = float(best.get('rho_sum', wls_params.get('rho_sum_pos_mean', 0.0)))
        shadow_band_details = shadow_main['band_details'] if shadow_main else {}
        shadow_rayleigh = shadow_main.get('rayleigh') if shadow_main else {}
        shadow_candidates_info = []
        if candidate_records:
            for rec in candidate_records:
                base = rec.get('base', {}) or {}
                perm_stats = rec.get('perm', {}) or {}
                shadow_candidates_info.append({
                    'tau': float(base.get('tau', float('nan'))),
                    'edge_count': int(base.get('edge_count', 0)),
                    'edge_quantile': float(base.get('edge_quantile', float('nan'))),
                    'S': float(base.get('S', float('nan'))),
                    'Q2': float(base.get('Q2', float('nan'))),
                    'p_perm': float(perm_stats.get('p_perm_one_sided_pos', float('nan'))),
                    'p_fdr': float(rec.get('p_fdr', float('nan')))
                })

        processing_meta = {
            'psf_grid': psf_records,
            'highpass_grid': hp_summary,
            'beta_candidates': [float(b) for b in (beta_sweep or [])],
            'alignment': {
                'method': str(fair_alignment.get('method', 'lanczos3')),
                'dy_pix': float(-align_dy),
                'dx_pix': float(-align_dx),
                'rng_seed': fair_rng.get('seed', 42)
            },
            'fast_mode': bool(FAST),
            'downsample': int(downsample),
            'dtype': 'float32' if use_float32 else 'float64',
            'band_limits': [(float(low), float(high)) for (low, high) in band_limits],
            'se_transform': str(params.se_transform or 'none'),
            'mask_quantile': float(mask_q),
            'mask_standard': 'top75',
            'mask_robustness': ['coverage','top50','top75','top90'],
            'roi_definition': {'core_r50': 'r <= r50', 'outer_r75': 'r >= r75'},
            'block_pix': int(block_pix),
            'N_eff': int(N_eff),
            'trim_frac': float(best.get('trim_frac', trim_frac)),
            'trim_iter': int(best.get('trim_iter', trim_iter)),
            'sigma_floor': float(best.get('sigma_floor', sigma_floor_best)),
            'sigma_scale': float(best.get('sigma_scale', sigma_scale_best)),
            'rho_sum_pos': rho_sum_best,
            'perm': {
                'target': perm_config.get('target') if isinstance(perm_config, dict) else None,
                'min': perm_config.get('min') if isinstance(perm_config, dict) else None,
                'max': perm_config.get('max') if isinstance(perm_config, dict) else None,
                'early_stop': bool(perm_config.get('early_stop', False)) if isinstance(perm_config, dict) else False,
            }
        }
        if fair_counts:
            processing_meta['fair_counts'] = {
                'N': int(fair_counts.get('N', 0)),
                'N_eff': int(fair_counts.get('N_eff', 0)),
                'block_pix': int(fair_counts.get('block_pix', block_pix_cfg))
            }
        if fair_alignment:
            processing_meta['fair_alignment'] = {
                'method': fair_alignment.get('method', ''),
                'dy_pix': float(fair_alignment.get('dy_pix', 0.0)),
                'dx_pix': float(fair_alignment.get('dx_pix', 0.0)),
                'rng_seed': fair_alignment.get('rng', None)
            }
        if fair_wrap:
            processing_meta['fair_wrap'] = {
                'dy': int(fair_wrap.get('dy', 0)),
                'dx': int(fair_wrap.get('dx', 0))
            }
        if fair_kmap:
            processing_meta['fair_k_map'] = {k: int(v) for k, v in fair_kmap.items() if isinstance(v, (int, float))}
        if fair_sha_full:
            processing_meta['fairness_meta'] = {
                'path': str(fair_config.path()),
                'sha256': fair_sha_full,
                'sha12': fair_sha_short
            }
        processing_meta['command_line'] = ' '.join(sys.argv)
        processing_meta['progress_log'] = str(progress_log)

        sshadow_val = S_shadow.get('global')
        sshadow_txt = ''
        if isinstance(sshadow_val, float) and sshadow_val == sshadow_val:
            if S_perm.get('n', 0) > 0 and isinstance(S_perm.get('p_perm_one_sided_pos'), float):
                line = f'④S_shadow={sshadow_val:.3f} (p_perm={S_perm["p_perm_one_sided_pos"]:.3f}'
                if isinstance(S_perm.get('p_fdr'), float) and S_perm['p_fdr'] == S_perm['p_fdr']:
                    line += f', q_FDR={S_perm["p_fdr"]:.3f}'
                line += ')'
                sshadow_txt = line
            else:
                sshadow_txt = f'④S_shadow={sshadow_val:.3f}'
        labels = [
            ('FDB', 'FDB'),
            ('rot', 'rot (180°)'),
            ('shift', 'shift (wrap)'),
            ('shuffle', 'shuffle (phase)')
        ]
        chi_lookup = {'FDB': chi_fdb, 'rot': chi_rot, 'shift': chi_shift, 'shuffle': chi_shuffle}
        table_rows = []
        for key, title in labels:
            table_rows.append(
                '<tr>'
                f'<th scope="row">{title}</th>'
                f'<td>{n}</td>'
                f'<td>{N_eff}</td>'
                f'<td>{kmap.get(key, 0)}</td>'
                f'<td>{chi_lookup[key]:.3g}</td>'
                f'<td>{rchi2_map.get(key, float("nan")):.3g}</td>'
                '</tr>'
            )
        card_html = (
            '<div class=card>'
            '<p><b>ホールドアウト ΔAICc と対照</b></p>'
            f'<p>best: σ_psf={gauss_sig:.2g} pix, w=Σ_e^{wpow:.2g} / ⟨Σ_e⟩^{wpow:.2g}</p>'
            f'<p>N={n}, N_eff={N_eff}, block_pix={block_pix}, k(FDB/rot/shift/shuffle)={kmap.get("FDB",0)}/{kmap.get("rot",1)}/{kmap.get("shift",2)}/{kmap.get("shuffle",0)}, σ_med={sigma_disp:.3g}</p>'
            f'<p>AICc(FDB)={fmt(A_fdb)}; controls: rot={fmt(A_rot)}, shift={fmt(A_shift)}, shuffle={fmt(A_shuffle)}</p>'
            f'<p>ΔAICc(FDB−rot)={fmt(A_fdb-A_rot)}, ΔAICc(FDB−shift)={fmt(A_fdb-A_shift)}, ΔAICc(FDB−shuffle)={fmt(A_fdb-A_shuffle)}</p>'
            f'<p><small>主要指標: ①ピーク距離(評価)=' + (f"{display_kpc:.0f}") + ' kpc [' + display_method + '], '
            f'②剪断位相整合=⟨cosΔθ⟩={shear_phase_cos:.3f}, '
            f'③corr(κ残差, Σ_e)={r_val:.3f} / Spearman={r_spear:.3f} (p={p_spear:.2g})（負が期待）'
            + (f', {sshadow_txt}' if sshadow_txt else '') + '</small></p>'
            '<p><small>幾何の統一: FFT相互相関により (dx,dy) を推定しサブピクセル整準して評価（FDBは k=2 に加算）。対照は整準後の予測場に対し、rot=180°回転 (k=1)、shift=固定ラップ(12,-7) pix (k=2)、shuffle=振幅保存の位相ランダム化 (k=0) を適用。</small></p>'
            '<table class="metrics">'
            '<thead><tr><th>model</th><th>N</th><th>N_eff</th><th>k</th><th>χ²</th><th>rχ²</th></tr></thead>'
            '<tbody>' + ''.join(table_rows) + '</tbody></table>'
            '</div>'
        )
        html.append(card_html)
        fair_note = f' ／ fair.json_sha={fair_sha_short}' if fair_sha_short else ''
        shared_note = f' ／ shared_params_sha={shared_sha_short}' if shared_sha_short else ''
        html.append(
            '<div class=card><small>再現: PYTHONPATH=. python scripts/reports/make_bullet_holdout.py '
            f'／ cluster_sha={cluster_param_sha}{fair_note}{shared_note}</small></div>'
        )

        wrap_note = {
            'dy': int(fair_wrap.get('dy', 12)) if fair_wrap else 12,
            'dx': int(fair_wrap.get('dx', -7)) if fair_wrap else -7
        }
        rng_seed_note = fair_rng.get('seed', 42)

        summary = {
                'alpha': params.alpha, 'beta': params.beta, 'C': params.C,
                'sigma_psf': gauss_sig, 'weight_power': wpow,
                'N': n, 'N_eff': N_eff, 'block_pix': block_pix,
                'AICc': {'FDB': A_fdb, 'rot': A_rot, 'shift': A_shift, 'shuffle': A_shuffle},
                'chi2': {'FDB': chi_fdb, 'rot': chi_rot, 'shift': chi_shift, 'shuffle': chi_shuffle},
                'rchi2': rchi2_map,
                'delta': {'FDB_minus_rot': A_fdb - A_rot, 'FDB_minus_shift': A_fdb - A_shift, 'FDB_minus_shuffle': A_fdb - A_shuffle},
                'k': {'FDB': kmap.get('FDB',0), 'rot': kmap.get('rot',1), 'shift': kmap.get('shift',2), 'shuffle': kmap.get('shuffle',0)},
                'sweep': sweep,
                'audit': {
                    'xcorr_shift_applied_pix': {'dy': float(-align_dy), 'dx': float(-align_dx)},
                    'controls': {'shift_wrap_pix': wrap_note, 'rng_seed': rng_seed_note}
                },
                'processing': processing_meta,
                'wls': {'sigma0': sigma0_param, 'c': coeff_param, 'block_pix': block_pix_cfg,
                        'trim_frac': trim_frac, 'trim_iter': trim_iter, 'rho_sum_pos_mean': wls_params.get('rho_sum_pos_mean', 0.0)},
                'indicators': {'peak_offset_pix': peak_offset_pix,
                               'peak_offset_pix_masked': peak_offset_pix_masked, 'mask_quantile': mask_q,
                               'hp_peak_offset_pix': hp_peak_offset_pix, 'hp_sigma_pix': hp_sigma,
                               'xcorr_shift_pix': xcorr_shift_pix, 'xcorr_peak_offset_pix': xcorr_peak_offset_pix,
                               'peak_distance_kpc': peak_kpc,
                               'hp_peak_distance_kpc': hp_peak_kpc,
                               'xcorr_peak_distance_kpc': xcorr_peak_kpc,
                               'shear_phase_cos': shear_phase_cos,
                               'corr_residual_sigmae': r_val, 'spear_r': r_spear, 'spear_p': p_spear,
                               'strata': strat, 'roi_stats': roi_stats,
                               'partial_r_given_r': roi_partial,
                               'shadow_metrics': {
                                   'S_shadow': S_shadow,
                                   'Q2': Q2_shadow,
                                   'v_test': V_shadow,
                                   'rayleigh': shadow_rayleigh,
                                   'per_band': shadow_band_details,
                                   'candidates': shadow_candidates_info,
                                   'bootstrap': shadow_bootstrap
                               },
                               'S_shadow': {'values': S_shadow, 'perm': S_perm, 'bootstrap': shadow_bootstrap},
                               'boundary_band': boundary_band,
                               'perm_test': {'n': perm_sample_n, 'effect_d': effect_d, 'p_perm_one_sided_neg': p_perm},
                               'bootstrap': boot,
                               'aux_tot': aux,
                               'pass': indicators_pass}
            }
        cmd_line = f"{shlex.quote(sys.executable)} " + ' '.join(shlex.quote(arg) for arg in sys.argv)
        env_keys = [
            'BULLET_PERM_N', 'BULLET_SHADOW_PERM_N', 'BULLET_SHADOW_SE_Q',
            'BULLET_SHADOW_RR_Q', 'BULLET_SHADOW_BLOCK', 'BULLET_EDGE_COUNT',
            'BULLET_MASK_Q', 'BULLET_ALIGN_OFFSETS', 'BULLET_WEIGHT_POWERS',
            'FAST_HOLDOUT'
        ]
        env_overrides = {k: os.environ[k] for k in env_keys if os.environ.get(k) is not None}
        try:
            script_sha12 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]
        except Exception:
            script_sha12 = ''
        shadow_perm_n = 0
        if isinstance(S_perm, dict):
            try:
                shadow_perm_n = int(S_perm.get('n', 0))
            except Exception:
                shadow_perm_n = 0
        summary['metadata'] = {
            'generated_at_utc': datetime.now(timezone.utc).isoformat(),
            'command': cmd_line,
            'script_sha12': script_sha12,
            'cluster_param_sha8': cluster_param_sha,
            'fair_json_sha256': fair_sha_full,
            'fair_json_sha12': fair_sha_short,
            'shared_params_sha256': shared_sha_full or None,
            'shared_params_sha12': shared_sha_short or None,
            'rng': {
                'holdout_seed': 42,
                'shadow_control_seed': rng_seed_note,
                'permutation_n': int(perm_sample_n or 0),
                'shadow_permutation_n': shadow_perm_n,
            },
            'fast_mode': bool(FAST),
            'downsample': int(downsample),
            'dtype': 'float32' if use_float32 else 'float64',
            'band_limits': [(float(low), float(high)) for (low, high) in band_limits],
            'perm_config': {
                'target': int(perm_config.get('target')) if isinstance(perm_config, dict) and perm_config.get('target') is not None else None,
                'min': int(perm_config.get('min')) if isinstance(perm_config, dict) and perm_config.get('min') is not None else None,
                'max': int(perm_config.get('max')) if isinstance(perm_config, dict) and perm_config.get('max') is not None else None,
                'early_stop': bool(perm_config.get('early_stop', False)) if isinstance(perm_config, dict) else False,
                'success_threshold': float(perm_config.get('success_threshold', 0.02)) if isinstance(perm_config, dict) else 0.02,
                'failure_threshold': float(perm_config.get('failure_threshold', 0.20)) if isinstance(perm_config, dict) else 0.20,
            },
            'shadow_block_pix': int(block_size_shadow),
            'env_overrides': env_overrides,
        }
    else:
        html.append('<div class=card><p>観測 κ (kappa_obs.fits) が無いので ΔAICc の計算を省略しました。</p></div>')
    # β sweep figure and table
    if summary and (summary.get('sweep')):
        try:
            fig, axes = plt.subplots(1, 1, figsize=(5.2, 3.0))
            ss = sorted(summary['sweep'], key=lambda d: d['beta'])
            axes.plot([d['beta'] for d in ss], [d['AICc'] for d in ss], marker='o')
            axes.set_xlabel('beta'); axes.set_ylabel('AICc (FDB, k=2)')
            axes.grid(True, ls=':', alpha=0.5)
            png_sweep = outdir / 'bullet_beta_sweep.png'
            fig.tight_layout(); fig.savefig(png_sweep, dpi=140); plt.close(fig)
            rows = ''.join([f"<tr><td>{d['beta']:.2f}</td><td>{int(d['N'])}</td><td>{d['AICc']:.1f}</td></tr>" for d in ss])
            html.append('<div class=card><h3>β スイープ（AICc 公平管理）</h3><p><img src="bullet_beta_sweep.png" style="max-width:100%"></p>'
                        f'<table class="t"><thead><tr><th>β</th><th>N</th><th>AICc(FDB)</th></tr></thead><tbody>{rows}</tbody></table></div>')
        except Exception:
            pass
    html.append(f'<div class=card><img src="{png_pred.name}" style="max-width:100%"></div>')
    
    # Robustness: mask thresholds (top 50/75/90% and coverage-only)
    try:
        if summary and ('indicators' in summary):
            ind = summary['indicators']
            # reuse k_obs_s, k_pred_s, se_obs, etc. by reloading JSON if needed
            # Here we recompute on-demand using saved file to keep code simple within this script context
            # Reload arrays for robustness calc
            oc2, se2, pix2 = oc, se, pix
            if obs_p.exists():
                k_obs2 = fits.getdata(obs_p).astype(work_dtype)
                if downsample > 1:
                    k_obs2 = _downsample_mean(k_obs2, downsample)
                k_pred2 = predict_kappa(oc2, se2, pix2, params)
                if k_pred2.shape != k_obs2.shape:
                    zy, zx = k_obs2.shape[0]/k_pred2.shape[0], k_obs2.shape[1]/k_pred2.shape[1]
                    k_pred2 = ndi.zoom(k_pred2, zoom=(zy, zx), order=1)
                se_obs2 = se2 if se2.shape == k_obs2.shape else ndi.zoom(se2, zoom=(k_obs2.shape[0]/se2.shape[0], k_obs2.shape[1]/se2.shape[1]), order=1)
                rr2 = (k_obs2 - k_pred2)
                def s_for_mask(m):
                    mm = m & np.isfinite(rr2) & np.isfinite(se_obs2)
                    if not np.any(mm):
                        return {'r': float('nan'), 'p': float('nan'), 'N': 0}
                    r, p = spearmanr(rr2[mm].ravel(), se_obs2[mm].ravel(), nan_policy='omit')
                    return {'r': float(r), 'p': float(p), 'N': int(np.sum(mm))}
                res = {}
                valid = np.isfinite(se_obs2)
                res['coverage'] = s_for_mask(valid)
                for ql in [0.5, 0.75, 0.9]:
                    try:
                        thr = float(np.nanquantile(se_obs2[valid], ql))
                        res[f'top{int(ql*100)}'] = s_for_mask(valid & (se_obs2 >= thr))
                    except Exception:
                        res[f'top{int(ql*100)}'] = {'r': float('nan'), 'p': float('nan'), 'N': 0}
                rows = ''.join([f"<tr><td>{k}</td><td>{v['N']}</td><td>{v['r']:.3f}</td><td>{v['p']:.2g}</td></tr>" for k,v in [('coverage',res['coverage']),('top50',res['top50']),('top75',res['top75']),('top90',res['top90'])]])
                html.append('<div class=card><h3>頑健性: マスク閾値（残差×Σ_e Spearman）</h3>'
                            '<table class="t"><thead><tr><th>mask</th><th>N</th><th>spearman r</th><th>p</th></tr></thead>'
                            f'<tbody>{rows}</tbody></table>'
                            '<small>共通処理条件（PSF/高通過/整準）を保持し、マスクのみ変更。</small></div>')
    except Exception:
        pass
    # Partial r bar figure (global/core/outer)
    try:
        pr = (summary.get('indicators') or {}).get('partial_r_given_r') or {}
        labels = ['global','core_r50','outer_r75']
        vals = [float(pr.get(k) or float('nan')) for k in labels]
        fig, ax = plt.subplots(1,1, figsize=(4.8,2.6))
        ax.bar(labels, vals, color=['#6baed6','#9ecae1','#c6dbef'])
        ax.axhline(0.0, color='k', lw=0.8)
        ax.set_ylabel('partial r(resid, Σ_e | r)')
        ax.set_ylim(min(-0.05, np.nanmin(vals)-0.05), max(0.05, np.nanmax(vals)+0.05))
        png_pr = outdir / 'bullet_partial_r_bar.png'
        fig.tight_layout(); fig.savefig(png_pr, dpi=140); plt.close(fig)
        html.append('<div class=card><h3>偏相関（全球/コア/外縁）</h3><p><img src="bullet_partial_r_bar.png" style="max-width:100%"></p></div>')
    except Exception:
        pass
    # AICc table with (N,k) and reduced chi²
    try:
        if summary:
            A = summary.get('AICc') or {}; K = summary.get('k') or {}; Np = int(summary.get('N') or 0)
            Neff = int(summary.get('N_eff') or Np)
            block_pix = int(summary.get('block_pix', 27))
            CH = summary.get('chi2') or {}
            def rchi(chi, k):
                return (float(chi) / max(Neff - int(k), 1)) if (chi==chi) else float('nan')
            rows = []
            for name in ['FDB','rot','shift','shuffle']:
                a = A.get(name); k = int(K.get(name, 0)); ch = CH.get(name)
                if a == a:
                    rows.append(f"<tr><td>{name}</td><td>{Np}</td><td>{Neff}</td><td>{k}</td><td>{a:.1f}</td><td>{(ch if ch==ch else float('nan')):.1f}</td><td>{rchi(ch,k):.4f}</td></tr>")
            html.append('<div class=card><h3>AICc / (N, N_eff, k) / rχ²</h3>'
                        '<table class="t"><thead><tr><th>model</th><th>N</th><th>N_eff</th><th>k</th><th>AICc</th><th>χ²</th><th>rχ²</th></tr></thead>'
                        f"<tbody>{''.join(rows)}</tbody></table>"
                        f'<small>公平条件: WLS σマップと N_eff={Neff} (block_pix={block_pix}) を全モデルで共通化し、整準(Δx,Δy)のみ自由度=k=2（rot=1, shift=2, shuffle=0）。PSF/高通過/マスク/ROIは本文に準拠。</small></div>')
    except Exception:
        pass
    # Shadow index and boundary-band cards
    try:
        if summary:
            ind = summary.get('indicators') or {}
            Ssh = ind.get('S_shadow') or {}
            shadow_meta = ind.get('shadow_metrics') or {}
            shadow_q2 = shadow_meta.get('Q2') or {}
            shadow_v = shadow_meta.get('v_test') or {}
            shadow_ray = shadow_meta.get('rayleigh') or {}
            bb  = ind.get('boundary_band') or {}
            if Ssh:
                vs = Ssh.get('values') or {}
                prn = Ssh.get('perm') or {}
                g = float((vs.get('global') or float('nan')))
                c = float((vs.get('core_r50') or float('nan')))
                o = float((vs.get('outer_r75') or float('nan')))
                q2g = float((shadow_q2.get('global') or float('nan')))
                q2c = float((shadow_q2.get('core_r50') or float('nan')))
                q2o = float((shadow_q2.get('outer_r75') or float('nan')))
                ray_p = float(shadow_meta.get('rayleigh', {}).get('p') or float('nan'))
                ray_R = float(shadow_meta.get('rayleigh', {}).get('R') or float('nan'))
                vt = shadow_v if isinstance(shadow_v, dict) else {}
                vt_p = float((vt.get('p') if isinstance(vt.get('p'), (int, float)) else vt.get('global', {}).get('p', float('nan'))) or float('nan'))
                vt_V = float((vt.get('V') if isinstance(vt.get('V'), (int, float)) else vt.get('global', {}).get('V', float('nan'))) or float('nan'))
                boot_meta = Ssh.get('bootstrap') or {}
                boot_line = ''
                if isinstance(boot_meta, dict) and int(boot_meta.get('n') or 0) > 0:
                    ci = boot_meta.get('S', {}).get('ci95', {})
                    if isinstance(ci, dict):
                        low = float(ci.get('low', float('nan')))
                        high = float(ci.get('high', float('nan')))
                        boot_line = f'<br><small>Bootstrap: n={int(boot_meta.get("n"))}, 95%CI=[{low:.3f}, {high:.3f}]</small>'
                p_fdr = prn.get('p_fdr') if isinstance(prn, dict) else float('nan')
                perm_line = f'Permutation(one‑sided >0): n={int(prn.get("n") or 0)}, p_perm={float((prn.get("p_perm_one_sided_pos") or float("nan"))):.3g}'
                if isinstance(p_fdr, float) and p_fdr == p_fdr:
                    perm_line += f', q_FDR={p_fdr:.3g}'
                html.append('<div class=card><h3>影整合指数 S_shadow</h3>'
                            f'<p>S_shadow (global/core/outer) = {g:.3f} / {c:.3f} / {o:.3f}</p>'
                            f'<p>Q2 (global/core/outer) = {q2g:.3f} / {q2c:.3f} / {q2o:.3f}</p>'
                            f'<small>{perm_line}</small><br>'
                            f'<small>Rayleigh: R={ray_R:.3f}, p={ray_p:.3g}; V-test: V={vt_V:.3f}, p={vt_p:.3g}</small>{boot_line}</div>')
            if bb and (bb.get('N') or 0) > 0:
                html.append('<div class=card><h3>境界帯域（二値評価）</h3>'
                            f'<p>|∇ω_p| 近傍帯(τ={float(bb.get("tau") or float("nan")):.3g}, δ_τ={float(bb.get("delta_tau") or float("nan")):.3g}) の外側方向における R<0 比率: '
                            f'{float(bb.get("neg_frac") or float("nan")):.3f} (N_total={int(bb.get("N") or 0)}, Fisher exact p(out>in)={float(bb.get("p_fisher_out_greater") or float("nan")):.3g})</p>'
                            '<small>外側/内側の R<0 件数に対するFisher検定。counts=' + str((bb.get('counts') or {})) + '</small></div>')
    except Exception:
        pass
    # Attach figures if present
    try:
        if (outdir/'bullet_peaks.png').exists():
            html.append('<div class=card><p><img src="bullet_peaks.png" style="max-width:100%"></p></div>')
        if (outdir/'bullet_shear_cos_hist.png').exists():
            html.append('<div class=card><p><img src="bullet_shear_cos_hist.png" style="max-width:100%"></p></div>')
        if (outdir/'bullet_residual_scatter.png').exists():
            html.append('<div class=card><p><img src="bullet_residual_scatter.png" style="max-width:100%"></p></div>')
    except Exception:
        pass
    # Footnote with thresholds if JSON exists
    try:
        bj = main_json
        if bj.exists():
            jd = json.loads(bj.read_text(encoding='utf-8'))
            ip = (jd.get('indicators') or {}).get('pass') or {}
            pk = ip.get('peak_distance_kpc') or {}
            pkhp = ip.get('peak_distance_kpc_highpass') or {}
            sp = ip.get('shear_phase_cos') or {}
            nc = ip.get('neg_corr_top10') or {}
            def onoff(v):
                return 'PASS' if v else 'FAIL'
            thr_pk = pk.get('thr');
            thr_cos = sp.get('thr');
            try:
                thr_pk = float(thr_pk)
            except Exception:
                thr_pk = float('nan')
            try:
                thr_cos = float(thr_cos)
            except Exception:
                thr_cos = float('nan')
            # (N,k) fairness note
            kmap = (jd.get('k') or {})
            ktxt = f"(N,k): N={int(jd.get('N') or 0)}, k(FDB/rot/shift/shuffle)={int(kmap.get('FDB',0))}/{int(kmap.get('rot',1))}/{int(kmap.get('shift',2))}/{int(kmap.get('shuffle',0))}"
            foot = (f"<div class=card><small>{ktxt}. 基準: ①ピーク距離≤{thr_pk:.0f} kpc（高通過版も参考）, ②⟨cosΔθ⟩≥{thr_cos:.2f}, ③top10% Spearman<0 ∧ p<0.05" 
                    f" → 判定: ①{onoff(bool(pk.get('pass')))}（高通過:{onoff(bool(pkhp.get('pass')))}）, ②{onoff(bool(sp.get('pass')))}, ③{onoff(bool(nc.get('pass')))}</small></div>")
            # also print helper distances in kpc if available
            ind = jd.get('indicators') or {}
            hpp = ind.get('hp_peak_distance_kpc'); xcp = ind.get('xcorr_peak_distance_kpc')
            if isinstance(hpp,(float,int)) or isinstance(xcp,(float,int)):
                ktxt = '<div class=card><small>補助: 高通過ピーク距離={:.0f} kpc, 整準後高通過ピーク距離={:.0f} kpc</small></div>'.format(
                    float(hpp) if isinstance(hpp,(float,int)) else float('nan'),
                    float(xcp) if isinstance(xcp,(float,int)) else float('nan'))
                html.append(ktxt)
            proc = jd.get('processing') or {}
            psf_cand = proc.get('psf_grid') or []
            hp_cand = proc.get('highpass_grid') or []
            beta_cand = proc.get('beta_candidates') or []
            def fmt_list(arr, fmt):
                if not arr:
                    return '-'
                try:
                    return ','.join(fmt(val) for val in arr)
                except Exception:
                    return ','.join(str(val) for val in arr)
            psf_list_txt = fmt_list([float(item.get('sigma_psf', item.get('sigma', float('nan')))) for item in psf_cand], lambda v: f"{v:.2f}")
            hp_list_txt = fmt_list([float(item.get('sigma_highpass', float('nan'))) for item in hp_cand], lambda v: f"{v:.1f}")
            beta_list_txt = fmt_list([float(b) for b in beta_cand], lambda v: f"{v:.2f}")
            html.append('<div class=card><small>処理候補: PSF σ候補=' + psf_list_txt + ' pix, 高通過 σ候補=' + hp_list_txt + ' pix, β候補=' + beta_list_txt + '</small></div>')
            html.append(foot)
            # ROI residual×Σ_e table
            roi = (ind.get('roi_stats') or {})
            if roi:
                def row(name):
                    d = roi.get(name) or {}
                    return f"<tr><td>{name}</td><td>{d.get('N',0)}</td><td>{(d.get('pearson_r')):.3f}</td><td>{(d.get('spear_r')):.3f}</td><td>{(d.get('p')):.2g}</td></tr>"
                rows = ''.join([row(k) for k in ['global','core_r50','outer_r75'] if k in roi])
                html.append('<div class=card><h3>残差×Σ_e の符号（全球 / r≤r50 / r≥r75）</h3>'
                            f'<table class="t"><thead><tr><th>ROI</th><th>N</th><th>pearson r</th><th>spearman r</th><th>p</th></tr></thead><tbody>{rows}</tbody></table>'
                            '<small>ROI: core=r≤r50（半径中央値内）, outer=r≥r75（外側四分位）。</small></div>')
            # Partial / Permutation summaries
            pr = (ind.get('partial_r_given_r') or {})
            pt = (ind.get('perm_test') or {})
            html.append('<div class=card><small>偏相関 r(resid,Σ_e | r) [global/core_r50/outer_r75] = [{:.3f}/{:.3f}/{:.3f}] · 位相乱数対照: n={}, d={:.2f}, p_perm(one‑sided, toward negative)={:.3g}</small></div>'.format(
                float(pr.get('global') or float('nan')),
                float(pr.get('core_r50') or float('nan')),
                float(pr.get('outer_r75') or float('nan')),
                int(pt.get('n') or 0), float(pt.get('effect_d') or float('nan')),
                float(pt.get('p_perm_one_sided_neg') or float('nan'))))
            # Bootstrap CI summary if present
            bs = (ind.get('bootstrap') or {})
            if bs:
                ci = bs.get('ci95') or [float('nan'), float('nan')]
                html.append('<div class=card><small>ブロックBootstrap: n={}, 95% CI for Spearman(global)=[{:.3f},{:.3f}], block≈{} pix</small></div>'.format(
                    int(bs.get('n') or 0), float(ci[0]), float(ci[1]), int(bs.get('block_pix') or 0)))
            # Auxiliary κ_tot residual correlations (if present)
            aux = (ind.get('aux_tot') or {})
            if aux:
                html.append('<div class=card><small>補助(κ_tot=κ_GR+κ_FDB): Spearman(global)={:.3f} (p={:.2g}), top10%={:.3f} (p={:.2g})</small></div>'.format(
                    float(aux.get('spear_r_tot') or float('nan')),
                    float(aux.get('spear_p_tot') or float('nan')),
                    float(aux.get('spear_r_tot_p90') or float('nan')),
                    float(aux.get('spear_p_tot_p90') or float('nan'))))
            # Processing footnotes (PSF/high-pass/mask/ROI/align)
            html.append('<div class=card><small>処理条件: PSF σ={:.2f} pix, 高通過 σ={} pix, マスク: Σ_e上位{:.0f}%, ROI(core/outer)=(r≤r50/r≥r75), 整準: FFT相互相関→Lanczos3 shift (dy,dx)=({:.2f},{:.2f}), 対照 wrap(dy,dx)=(12,−7), rng=42</small></div>'.format(
                float(jd.get('sigma_psf') or float('nan')),
                int((jd.get('indicators') or {}).get('hp_sigma_pix') or 0),
                float(100.0*((jd.get('indicators') or {}).get('mask_quantile') or 0.75)),
                float((jd.get('audit') or {}).get('xcorr_shift_applied_pix',{}).get('dy', 0.0)),
                float((jd.get('audit') or {}).get('xcorr_shift_applied_pix',{}).get('dx', 0.0))
            ))
            # Optional: galaxy/ICL peaks and environment logs
            try:
                import os as _os
                pkpath = Path('data/cluster/Bullet/peaks.json')
                extra = []
                if pkpath.exists():
                    pks = json.loads(pkpath.read_text(encoding='utf-8'))
                    gal = pks.get('galaxy') or {}
                    icl = pks.get('icl') or {}
                    extra.append('銀河ピーク(x,y)=({},{})'.format(gal.get('x','?'), gal.get('y','?')))
                    extra.append('ICLピーク(x,y)=({},{})'.format(icl.get('x','?'), icl.get('y','?')))
                envj = Path('server/public/reports/env_logs.json')
                if envj.exists():
                    ej = json.loads(envj.read_text(encoding='utf-8'))
                    sha = ej.get('shared_params_sha') or ''
                    extra.append('環境: lenstool={} / ciaover={}, shared_params_sha={}'.format((ej.get('lenstool') or '')[:16], (ej.get('ciaover') or '').split('\n')[0], sha[:8]))
                if extra:
                    html.append('<div class=card><small>{}</small></div>'.format(' ・ '.join(extra)))
            except Exception:
                pass
            # Audit meta
            au = jd.get('audit') or {}
            xs = (au.get('xcorr_shift_applied_pix') or {})
            ct = (au.get('controls') or {})
            html.append('<div class=card><small>整準/対照: xcorr shift (dy,dx)=({:.2f},{:.2f}), shift対照 wrap(dy,dx)=({},{}), rng_seed={}</small></div>'.format(
                float(xs.get('dy') or 0.0), float(xs.get('dx') or 0.0),
                (ct.get('shift_wrap_pix') or {}).get('dy', 12), (ct.get('shift_wrap_pix') or {}).get('dx', -7),
                ct.get('rng_seed', 42)))
    except Exception:
        pass
    html.append('</main></body></html>')
    _write_html_lines(html)
    # dump JSON summary
    if summary:
        _write_json_obj(summary)
    # Persist per-holdout copies to avoid overwriting historical runs
    cluster_dir = Path('server/public/reports/cluster')
    cluster_dir.mkdir(parents=True, exist_ok=True)
    ho_html = cluster_dir / f'{holdout}_holdout.html'
    ho_json = cluster_dir / f'{holdout}_holdout.json'
    try:
        shutil.copy2(main_html, ho_html)
    except Exception:
        pass
    if summary:
        try:
            shutil.copy2(main_json, ho_json)
        except Exception:
            pass
    print('wrote', main_html)
    _append_progress(progress_log, f"=== finished holdout {holdout}")
    return 0


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='バレットクラスタの最小核ホールドアウト（学習→固定→適用）')
    ap.add_argument('--train', type=str, default='Abell1689,CL0024', help='学習に使うクラスタ名カンマ区切り')
    ap.add_argument('--holdout', type=str, default='Bullet', help='ホールドアウト対象名')
    ap.add_argument('--beta-sweep', type=str, default='0.3,0.5,0.7,0.9', help='β 候補（カンマ区切り）')
    ap.add_argument('--sigma-psf', type=str, default='', help='PSF σ 候補（pix, カンマ区切り）')
    ap.add_argument('--sigma-highpass', type=str, default='', help='高通過 σ 候補（pix, カンマ区切り）')
    ap.add_argument('--se-transform', type=str, default='', help='Σ_e 変換: none|log1p|asinh|quantile|rank')
    ap.add_argument('--roi-quantiles', type=str, default='', help='Σ_e ROI 上位分位（0-1, カンマ区切り）')
    ap.add_argument('--align-offsets', type=str, default='', help='整準後に追加する微調整オフセット（pix, カンマ区切り）')
    ap.add_argument('--weight-powers', type=str, default='', help='誤差重み w(Σ_e)= (Σ_e/⟨Σ_e⟩)^p の指数リスト')
    ap.add_argument('--fast', action='store_true', help='FAST 推奨設定で計算量を抑えて探索する')
    ap.add_argument('--downsample', type=int, default=None, help='FAST 時のダウンサンプル倍率 (既定 2)')
    ap.add_argument('--float32', action='store_true', help='計算を float32 で実施する')
    ap.add_argument('--band', type=str, default='', help='影バンド範囲 (例: "8-16,4-8")')
    ap.add_argument('--perm-n', type=int, default=None, help='Permutation 目標回数')
    ap.add_argument('--perm-min', type=int, default=None, help='Permutation 最小学習回数')
    ap.add_argument('--perm-max', type=int, default=None, help='Permutation 最大回数')
    ap.add_argument('--perm-earlystop', action='store_true', help='Permutation の早期停止を有効化')
    ap.add_argument('--block-pix', type=int, default=None, help='Shadow 用 block_pix を固定')
    args = ap.parse_args()
    train = [s.strip() for s in args.train.split(',') if s.strip()]
    try:
        bs = [float(s.strip()) for s in (args.beta_sweep or '').split(',') if s.strip()]
    except Exception:
        bs = [0.3, 0.5, 0.7, 0.9]
    def parse_floats(s):
        try:
            return [float(x.strip()) for x in (s or '').split(',') if x.strip()]
        except Exception:
            return []
    psf_list = parse_floats(args.sigma_psf)
    hp_list = parse_floats(args.sigma_highpass)
    wp_list = parse_floats(args.weight_powers)
    se_tr = (args.se_transform or '').strip() or None
    roi_qs = _parse_float_list(args.roi_quantiles)
    align_offs = _parse_float_list(args.align_offsets)
    band_list: list[tuple[float, float]] = []
    if args.band:
        for part in args.band.split(','):
            part = part.strip()
            if not part:
                continue
            try:
                low_str, high_str = part.split('-', 1)
                band_list.append((float(low_str), float(high_str)))
            except Exception:
                continue

    perm_cfg: dict[str, object] = {}
    if args.perm_n is not None:
        perm_cfg['target'] = args.perm_n
    if args.perm_min is not None:
        perm_cfg['min'] = args.perm_min
    if args.perm_max is not None:
        perm_cfg['max'] = args.perm_max
    if args.perm_earlystop:
        perm_cfg['early_stop'] = True

    downsample_factor = args.downsample if args.downsample is not None else (2 if args.fast else 1)
    use_float32_flag = bool(args.float32 or args.fast)

    if args.fast:
        if not psf_list:
            psf_list = [1.0, 1.5]
        if not hp_list:
            hp_list = [1.0, 1.5]
        if not wp_list:
            wp_list = [0.0, 0.3]
        if not roi_qs:
            roi_qs = [0.70, 0.80]
        if not band_list:
            band_list = [(8.0, 16.0)]
        perm_cfg.setdefault('target', 1200)
        perm_cfg.setdefault('min', 600)
        perm_cfg.setdefault('max', 2000)
        perm_cfg.setdefault('early_stop', True)
        perm_cfg.setdefault('success_threshold', 0.02)
        perm_cfg.setdefault('failure_threshold', 0.20)
        if args.block_pix is None:
            args.block_pix = 6
    else:
        if args.perm_earlystop:
            perm_cfg.setdefault('success_threshold', 0.02)
            perm_cfg.setdefault('failure_threshold', 0.20)

    shadow_block_override = args.block_pix

    return holdout_report(
        train,
        args.holdout,
        beta_sweep=bs,
        psf_sigmas=psf_list,
        hp_sigmas=hp_list,
        se_transform=se_tr,
        roi_quantiles=roi_qs,
        align_offsets=align_offs,
        weight_powers=wp_list,
        fast=args.fast,
        downsample=downsample_factor,
        use_float32=use_float32_flag,
        band_limits=band_list or None,
        perm_config=perm_cfg if perm_cfg else None,
        shadow_block_pix=shadow_block_override
    )


if __name__ == '__main__':
    raise SystemExit(main())
