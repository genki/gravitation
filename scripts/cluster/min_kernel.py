#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from typing import Tuple


@dataclass
class MinKernelParams:
    alpha: float = 1.0   # attenuation term: exp(-α Σ_e)
    beta: float = 0.3    # forwardization in S (Lambert→β)
    C: float = 0.0       # optional isotropic 1/θ term weight
    # Re-emission term parameters (W_eff = exp(-α Σ_e) + ξ Σ_e^p)
    xi: float = 0.0
    p: float = 0.5
    # Gradient-gate parameters on ω_proxy (|∇ω_p|)
    tau_q: float = 0.7        # τ = q-quantile(|∇ω_p|)
    delta_tau_frac: float = 0.1  # δτ = frac * τ
    # Sigma_e quantile normalization (scale Σ_e by q-th quantile)
    sigma_norm_q: float = 0.9
    # Optional Σ_e transform prior to normalization: none|log1p|asinh|quantile|rank
    se_transform: str = 'none'
    # Interface gate global scaling factor (counts as a hyperparam in training)
    s_gate: float = 1.0
    # Re-emission saturation scale in normalized Σ_e units (∞ = no saturation)
    xi_sat: float = 1e12
    # Re-emission knee as quantile in [0,1]; <0 disables knee
    q_knee: float = -1.0
    # Multi-scale gradient-gate sigmas (pixels); empty → single-scale (native)
    gate_sigmas: tuple = (2.0, 4.0, 8.0)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _unit_vectors(h: int, w: int, pix: float) -> Tuple[np.ndarray, np.ndarray]:
    cy = (h - 1) / 2.0; cx = (w - 1) / 2.0
    yy, xx = np.mgrid[0:h, 0:w]
    dx = (xx - cx) * pix; dy = (yy - cy) * pix
    rr = np.hypot(dx, dy) + 1e-30
    rhatx = dx / rr; rhaty = dy / rr
    return rhatx, rhaty


def kernel_inv_theta(h: int, w: int, pix: float) -> np.ndarray:
    """2D kernel ~ 1/θ (≈ 1/R in pixels)."""
    cy = (h - 1) / 2.0; cx = (w - 1) / 2.0
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.hypot(xx - cx, yy - cy) * pix
    k = 1.0 / np.clip(r, 1e-3 * pix, None)
    k[int(cy), int(cx)] = k[int(cy), int(cx) + 1]  # avoid inf
    return k


def fft_convolve2d(a: np.ndarray, k: np.ndarray) -> np.ndarray:
    import numpy.fft as nf
    H, W = a.shape
    fH = int(2 ** np.ceil(np.log2(H * 1.5)))
    fW = int(2 ** np.ceil(np.log2(W * 1.5)))
    Af = nf.rfftn(a, s=(fH, fW))
    Kf = nf.rfftn(k, s=(fH, fW))
    out = nf.irfftn(Af * Kf, s=(fH, fW))[:H, :W]
    return out


def predict_kappa(omega_cut: np.ndarray,
                  sigma_e: np.ndarray,
                  pix: float,
                  params: MinKernelParams) -> np.ndarray:
    """Compute κ_FDB ≈ (W_eff · S) * K with minimal kernel.

    - W_eff(Σ_e) = exp(-α Σ_e) + ξ Σ_e^p
    - S = σ(((|∇ω_p| − τ)/δτ)) · [n·rhat]_+ · max(0, 1 + β cos Θ)
      where τ is the tau_q-quantile of |∇ω_p| and δτ = delta_tau_frac · τ
    - K ≈ 1/θ (2D)
    """
    from numpy import exp, clip
    H, W = omega_cut.shape
    # normals via central differences on ω_cut proxy (multi-scale support)
    def grad_mag(arr: np.ndarray, sigma: float | None = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        from scipy import ndimage as _ndi
        if sigma and sigma > 0:
            arr = _ndi.gaussian_filter(arr, sigma=sigma)
        gy, gx = np.gradient(arr, pix, pix)
        gmag = np.hypot(gx, gy)
        return gy, gx, gmag
    gy, gx, gmag0 = grad_mag(omega_cut, None)
    # multi-scale: take max magnitude over provided sigmas
    gmag = gmag0
    try:
        gs = list(getattr(params, 'gate_sigmas', ()) or [])
    except Exception:
        gs = []
    if gs:
        for s in gs:
            try:
                _, _, gm = grad_mag(omega_cut, float(s))
                gmag = np.maximum(gmag, gm)
            except Exception:
                continue
    nrm = np.hypot(gx, gy) + 1e-30
    nx = gx / nrm; ny = gy / nrm
    rhatx, rhaty = _unit_vectors(H, W, pix)
    cos_th = clip(nx * rhatx + ny * rhaty, -1.0, 1.0)
    lambert = 1.0 + float(params.beta) * cos_th
    lambert = np.clip(lambert, 0.0, None)
    # Gradient-gate with quantile threshold
    try:
        tau = float(np.nanquantile(gmag[np.isfinite(gmag)], float(params.tau_q)))
    except Exception:
        tau = float(np.nanmedian(gmag[np.isfinite(gmag)])) if np.any(np.isfinite(gmag)) else 0.0
    dtau = max(float(params.delta_tau_frac) * max(tau, 1e-12), 1e-12)
    gate = _sigmoid((gmag - tau) / dtau)
    S = float(getattr(params, 's_gate', 1.0)) * gate * np.maximum(0.0, cos_th) * lambert
    # W_eff with optional transform + quantile normalization of Σ_e + knee
    sig = np.clip(sigma_e, 0.0, None)
    tf = (getattr(params, 'se_transform', 'none') or 'none').lower()
    if tf in {'identity', 'id'}:
        tf = 'none'
    if tf == 'log1p':
        sig = np.log1p(sig)
    elif tf == 'asinh':
        sig = np.arcsinh(sig)
    elif tf == 'quantile':
        flat = sig[np.isfinite(sig)].ravel()
        if flat.size:
            order = np.argsort(flat)
            ranks = np.empty_like(order, dtype=float)
            ranks[order] = (np.arange(order.size, dtype=float) + 0.5) / float(order.size)
            sig[np.isfinite(sig)] = ranks
    elif tf == 'rank':
        flat = sig[np.isfinite(sig)].ravel()
        if flat.size:
            order = np.argsort(flat)
            inv = np.empty_like(order)
            inv[order] = np.arange(order.size)
            ranks = (inv.astype(float) + 0.5) / float(order.size)
            sig[np.isfinite(sig)] = ranks
    try:
        q = float(getattr(params, 'sigma_norm_q', 0.9))
    except Exception:
        q = 0.9
    try:
        qv = float(np.nanquantile(sig[np.isfinite(sig)], q)) if np.any(np.isfinite(sig)) else 1.0
    except Exception:
        qv = 1.0
    if not np.isfinite(qv) or qv <= 0:
        qv = 1.0
    sig = sig / qv
    # Knee in normalized space: subtract Σ_{q_knee}
    try:
        qk = float(getattr(params, 'q_knee', -1.0))
    except Exception:
        qk = -1.0
    if 0.0 <= qk <= 1.0:
        try:
            knee_val = float(np.nanquantile(sig[np.isfinite(sig)], qk))
        except Exception:
            knee_val = 0.0
        sig_k = np.clip(sig - knee_val, 0.0, None)
    else:
        sig_k = sig
    W_att = np.exp(-float(params.alpha) * sig)
    # Saturating re-emission: xi * sig^p / (1 + sig/xi_sat)
    if float(params.xi) != 0.0:
        sat = float(getattr(params, 'xi_sat', 1e12))
        if sat <= 0:
            sat = 1e12
        W_re_core = np.power(sig_k, float(params.p))
        if np.isfinite(sat) and sat < 1e11:
            W_re_core = W_re_core / (1.0 + (sig / sat))
        W_re = float(params.xi) * W_re_core
    else:
        W_re = 0.0
    Ww = W_att + W_re
    WS = Ww * S
    K = kernel_inv_theta(H, W, pix)
    kappa = fft_convolve2d(WS, K)
    if params.C != 0.0:
        kappa = kappa + float(params.C) * fft_convolve2d(np.ones_like(WS), K)
    return kappa
