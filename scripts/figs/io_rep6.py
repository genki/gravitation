#!/usr/bin/env python3
from __future__ import annotations

"""Common IO and model helpers for rep6 plotting under fair conditions.

Models supported: GR (baryons), MOND, GRDM(NFW prior), FDB_WS (surface W·S),
FDB_IF (Phi·eta from Halpha/proxy). Returns Total/Isotropic/Add components and meta.

All statistics use the site-wide error-floor policy:
  dV_floor = clip(0.03*|Vobs|, 3..7) [km/s]
and are computed in acceleration space with identical N across compared models.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple, Optional
import math
import numpy as np
from astropy.io import fits

from scripts.fit_sparc_fdbl import read_sparc_massmodels
from scripts.compare_fit_multi import to_accel, line_bias_accel
from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_profile_from_map

M_PER_KM = 1.0e3
KPC_IN_M = 3.08567758149137e19
A0_SI = 1.2e-10
A0_KPC = A0_SI * (KPC_IN_M / (M_PER_KM ** 2))  # (km^2 s^-2)/kpc


@dataclass
class Observed:
    R: np.ndarray
    V: np.ndarray
    eV: np.ndarray


def _error_floor(V: np.ndarray) -> np.ndarray:
    return np.clip(0.03 * np.abs(V), 3.0, 7.0)


def load_observed(galaxy: str) -> Observed:
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), galaxy)
    return Observed(R=rc.R.astype(float), V=rc.Vobs.astype(float), eV=np.maximum(rc.eV, 1e-6).astype(float))


def _load_halpha_or_proxy(name: str) -> Tuple[np.ndarray, float]:
    p = Path(f'data/halpha/{name}/Halpha_SB.fits')
    if p.exists():
        img = fits.getdata(p).astype(float)
        hdr = fits.getheader(p)
        pix = float(hdr.get('PIXSCALE', 0.305)) / 206265.0
        if not np.isfinite(pix) or pix <= 0:
            pix = 0.2
        # downsample oversize maps
        maxdim = max(img.shape)
        if maxdim > 1200:
            import scipy.ndimage as ndi
            scale = 800.0 / maxdim
            img = ndi.zoom(img, zoom=scale, order=1)
            pix = pix / scale
        return img, pix
    # proxy from SBdisk (axisymmetric)
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    # build 2D from SBdisk via radial interp
    size = 256; pix = 0.2
    y = (np.arange(size) - (size - 1) / 2.0) * pix
    x = (np.arange(size) - (size - 1) / 2.0) * pix
    yy, xx = np.meshgrid(y, x, indexing='ij')
    rr = np.hypot(xx, yy)
    img = np.interp(rr.ravel(), rc.R, rc.SBdisk, left=rc.SBdisk[0], right=rc.SBdisk[-1]).reshape(size, size)
    m = float(np.nanmax(img))
    if m > 0:
        img = img / m
    return img, pix


def _fair_mask(*arrs: np.ndarray) -> np.ndarray:
    m = np.ones_like(arrs[0], dtype=bool)
    for a in arrs:
        m &= np.isfinite(a)
    return m


def _fit_mu_alpha(g_obs: np.ndarray, eg: np.ndarray, g_star: np.ndarray, g_extra: Optional[np.ndarray], g_gas: np.ndarray) -> Tuple[float, float]:
    # Weighted least squares for [mu, alpha] in g_model = g_gas + mu*g_star + alpha*g_extra
    if g_extra is None:
        # alpha=0; solve mu only
        y = g_obs - g_gas
        x = g_star
        w = 1.0 / np.maximum(eg, 1e-6)
        num = float(np.nansum(w * x * y))
        den = float(np.nansum(w * x * x))
        mu = num / max(den, 1e-30)
        return float(max(mu, 0.0)), 0.0
    w = 1.0 / np.maximum(eg, 1e-6)
    X1 = g_star; X2 = g_extra; Y = g_obs - g_gas
    S11 = float(np.nansum(w * X1 * X1)); S22 = float(np.nansum(w * X2 * X2)); S12 = float(np.nansum(w * X1 * X2))
    b1 = float(np.nansum(w * X1 * Y));  b2 = float(np.nansum(w * X2 * Y))
    det = S11 * S22 - S12 * S12
    if det <= 0:
        return 0.7, 0.0
    mu = (b1 * S22 - b2 * S12) / det
    alpha = (S11 * b2 - S12 * b1) / det
    return float(mu), float(alpha)


def _aicc(chi2: float, k: int, N: int) -> float:
    return float(chi2 + (2 * k * (k + 1)) / max(N - k - 1, 1))


def load_model(galaxy: str, model: str) -> Dict[str, object]:
    """Return dict with V_total, V_iso, V_add, meta for the requested model.

    Model keys: "GR", "MOND", "GRDM", "FDB_WS", "FDB_IF".
    """
    model = model.upper()
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), galaxy)
    R = rc.R.astype(float); Vobs = rc.Vobs.astype(float)
    eV_raw = np.maximum(rc.eV, 1e-6).astype(float)
    floor = _error_floor(Vobs)
    eV_eff = np.sqrt(eV_raw * eV_raw + floor * floor)
    g_obs, eg = to_accel(R, Vobs, eV_eff)
    Rm = np.maximum(R, 1e-6)
    g_gas = (1.33 * (rc.Vgas * rc.Vgas)) / Rm
    g_star0 = (rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul) / Rm

    # Helper to build outputs
    def pack(g_iso: np.ndarray, g_add: np.ndarray, k: int, extra_meta: Dict[str, object]) -> Dict[str, object]:
        g_total = g_gas + g_iso + g_add
        m = _fair_mask(g_obs, eg, g_total)
        N = int(np.sum(m))
        chi = float(np.nansum(((g_total[m] - g_obs[m]) / np.maximum(eg[m], 1e-6)) ** 2))
        out = {
            'V_total': np.sqrt(np.maximum(g_total * Rm, 0.0)),
            'V_iso': np.sqrt(np.maximum((g_gas + g_iso) * Rm, 0.0)),
            'V_add': np.sqrt(np.maximum(g_add * Rm, 0.0)),
            'meta': {
                'N': N,
                'k': int(k),
                'chi2': chi,
                'rchi2': float(chi / max(N - k, 1)),
                'AICc': _aicc(chi, int(k), N),
                **extra_meta,
            }
        }
        return out

    if model == 'GR':
        mu, _ = _fit_mu_alpha(g_obs, eg, g_star0, None, g_gas)
        g_iso = mu * g_star0
        return pack(g_iso, np.zeros_like(g_iso), k=1, extra_meta={'mu': float(mu)})

    if model == 'MOND':
        # Fit mu for stellar M/L; MOND g = (aN/2)+sqrt((aN/2)^2 + aN*a0)
        def chi_for_mu(mu: float) -> float:
            aN = g_gas + mu * g_star0
            half = 0.5 * aN
            gM = half + np.sqrt(np.maximum(half * half + aN * A0_KPC, 0.0))
            m = _fair_mask(g_obs, eg, gM)
            return float(np.nansum(((gM[m] - g_obs[m]) / np.maximum(eg[m], 1e-6)) ** 2))
        # scan a small set around 0.6–1.2
        grid = np.linspace(0.3, 1.2, 19)
        chi_vals = [chi_for_mu(mu) for mu in grid]
        mu = float(grid[int(np.argmin(np.asarray(chi_vals)))])
        aN = g_gas + mu * g_star0
        half = 0.5 * aN
        gM = half + np.sqrt(np.maximum(half * half + aN * A0_KPC, 0.0))
        return pack(mu * g_star0, gM - (g_gas + mu * g_star0), k=1, extra_meta={'mu': mu})

    if model == 'GRDM':
        # NFW grid with c–M prior penalty; ref: benchmarks/plot_rep_fig.py
        def nfw_velocity(R: np.ndarray, V200: float, c: float) -> np.ndarray:
            G = 4.30091e-6  # kpc km^2 / (s^2 Msun)
            H0 = 70.0  # km/s/Mpc
            rho_c = 3 * (H0 / 1000.0) ** 2 / (8 * math.pi * G)
            delta_c = 200.0 / 3.0 * (c ** 3) / (math.log(1 + c) - c / (1 + c))
            Rvir = V200 / (10 * H0 / 1000.0)
            rs = Rvir / c
            x = np.maximum(R / rs, 1e-8)
            M_enclosed = 4 * math.pi * delta_c * rho_c * rs ** 3 * (np.log(1 + x) - x / (1 + x))
            return np.sqrt(np.maximum(G * M_enclosed / np.maximum(R, 1e-6), 0.0))
        def cM_expected(V200: float) -> float:
            # crude reference relation
            return max(5.0, min(20.0, 10.0 + 0.02 * (V200 - 160.0)))
        best = (math.inf, 120.0, 10.0, 0.7)
        for V200 in [80, 120, 160, 200, 240, 280]:
            for c in [5.0, 7.0, 10.0, 12.0, 15.0, 20.0]:
                Vdm = nfw_velocity(R, V200, c)
                g_dm = (Vdm * Vdm) / Rm
                mu, _ = _fit_mu_alpha(g_obs, eg, g_star0, g_dm, g_gas)
                g_model = g_gas + mu * g_star0 + g_dm
                m = _fair_mask(g_obs, eg, g_model)
                chi = float(np.nansum(((g_model[m] - g_obs[m]) / np.maximum(eg[m], 1e-6)) ** 2))
                # c–M prior in chi-space (ln c Gaussian)
                c_exp = cM_expected(V200)
                sigma_ln_c = 0.35
                chi_eff = chi + ((math.log(max(c, 1e-6)) - math.log(c_exp)) / sigma_ln_c) ** 2
                if chi_eff < best[0]:
                    best = (chi_eff, V200, c, mu)
        _, V200_b, c_b, mu_b = best
        Vdm_b = nfw_velocity(R, V200_b, c_b)
        g_dm_b = (Vdm_b * Vdm_b) / Rm
        return pack(mu_b * g_star0, g_dm_b, k=3, extra_meta={'V200': V200_b, 'c': c_b, 'mu': mu_b})

    if model in ('FDB_WS', 'FDB_IF'):
        if model == 'FDB_WS':
            g_extra = line_bias_accel(R, rc.SBdisk, pix_kpc=0.2, size=256, line_eps_kpc=0.8, pad_factor=2)
            meta_extra = {'kind': 'WS', 'eps_kpc': 0.8}
        else:
            img, pix = _load_halpha_or_proxy(galaxy)
            k_grid = np.linspace(0.02, 1.0, 24)
            best = None
            for beta in (0.0, 0.3, 0.6):
                g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid,
                                                  phi_k=np.exp(-(k_grid/0.6)**2), eta_params=EtaParams(beta=beta, s_kpc=0.5))
                m = _fair_mask(g_obs, eg, g_if)
                mu, alpha = _fit_mu_alpha(g_obs[m], eg[m], g_star0[m], g_if[m], g_gas[m])
                g_model = (g_gas + mu * g_star0 + alpha * g_if)
                chi = float(np.nansum(((g_model[m] - g_obs[m]) / np.maximum(eg[m], 1e-6)) ** 2))
                row = (chi, mu, alpha, beta, g_if)
                if (best is None) or (row[0] < best[0]):
                    best = row
            assert best is not None
            chi, mu_b, alpha_b, beta_b, g_extra = best
            meta_extra = {'kind': 'IF', 'beta': float(beta_b)}
            # proceed to pack below with fitted mu/alpha using g_extra
        # Common path: fit mu/alpha on full mask
        m = _fair_mask(g_obs, eg, g_extra)
        mu, alpha = _fit_mu_alpha(g_obs[m], eg[m], g_star0[m], g_extra[m], g_gas[m])
        return pack(mu * g_star0, alpha * g_extra, k=2, extra_meta={'mu': float(mu), 'alpha': float(alpha), **meta_extra})

    raise ValueError(f'unknown model: {model}')

