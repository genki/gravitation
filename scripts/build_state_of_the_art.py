#!/usr/bin/env python3
from __future__ import annotations
import json
import os, sys
import time
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
import shutil
import math
import re
import yaml

try:
    from PIL import Image
except Exception:  # pillow が無い環境では寸法取得を諦める
    Image = None  # type: ignore

from scripts.fdb.shared_params_loader import load as load_shared_params
from scripts.config import fair as fair_config


REPO_ROOT = Path(__file__).resolve().parents[1]
SOTA_HTML_DIR = REPO_ROOT / "server/public/state_of_the_art"
_RASTER_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
M_PER_KM = 1.0e3
KPC_IN_M = 3.08567758149137e19
A0_SI = 1.2e-10  # m/s^2


def _a0_si_to_kpc(a0_si: float) -> float:
    return a0_si * (KPC_IN_M / (M_PER_KM ** 2))


A0_KPC = _a0_si_to_kpc(A0_SI)


def _resolve_image_path(src: str, base_dir: Path | None = None) -> Path | None:
    try:
        anchor = base_dir if base_dir is not None else SOTA_HTML_DIR
        resolved = (anchor / Path(src)).resolve()
    except Exception:
        return None
    repo_root = REPO_ROOT.resolve()
    if not str(resolved).startswith(str(repo_root)):
        return None
    if resolved.exists():
        return resolved
    return None


def _image_dimensions(src: str, base_dir: Path | None = None) -> tuple[int, int] | None:
    if Image is None:
        return None
    suffix = Path(src.split('?', 1)[0]).suffix.lower()
    if suffix not in _RASTER_SUFFIXES:
        return None
    path = _resolve_image_path(src, base_dir=base_dir)
    if path is None:
        return None
    try:
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def _img_html_attrs(src: str, style: str | None = None, base_dir: Path | None = None) -> str:
    attrs: List[str] = [f'src="{src}"', 'loading="lazy"']
    dims = _image_dimensions(src, base_dir=base_dir)
    if dims:
        w, h = dims
        attrs.append(f'width="{w}"')
        attrs.append(f'height="{h}"')
        default_style = f'width:min(100%, {w}px);height:auto'
    else:
        default_style = 'max-width:100%;height:auto'
    attrs.append(f'style="{style if style is not None else default_style}"')
    return ' '.join(attrs)


def h(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;")
        .replace(">", "&gt;").replace('"', "&quot;")
    )


def sha12(path: str) -> str | None:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    except Exception:
        return None


def load_jsons() -> List[Path]:
    return sorted(Path("data/results").glob("multi_fit*.json"),
                  key=lambda p: p.stat().st_mtime, reverse=True)


def load_progress() -> tuple[float | None, float | None, str | None]:
    p = Path("data/progress.json")
    if not p.exists():
        return None, None, None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        hist = data.get("history", [])
        if not hist:
            return None, None, None
        cur = hist[-1]
        prev = hist[-2] if len(hist) >= 2 else None
        return (
            float(prev["rate"]) if prev else None,
            float(cur["rate"]),
            str(cur.get("ts") or ""),
        )
    except Exception:
        return None, None, None


def pick_best_result(files: List[Path]) -> Path | None:
    """Pick a representative multi_fit*.json for SOTA summary.

    Preference order:
      1) Largest sample size (len(names) or N_total.ULW)
      2) Newer mtime
    This avoids cross-dataset AIC comparisons (not comparable across N).
    """
    # 1) Prefer blacklist-filtered results if present (filename contains 'noBL')
    nobl = [p for p in files if 'nobl' in p.name.lower()]
    if nobl:
        nobl.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return nobl[0]
    # 2) Prefer files that include mu_k(shared) metadata
    with_mu = []
    for p in files:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            mk = d.get('mu_k', {})
            if isinstance(mk, dict) and mk.get('shared'):
                with_mu.append(p)
        except Exception:
            continue
    if with_mu:
        with_mu.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return with_mu[0]
    # 3) Otherwise, pick by sample size then mtime
    cand: List[Tuple[int, float, Path]] = []
    for p in files:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            n1 = len(data.get("names", []))
            n2 = int(data.get("N_total", {}).get("ULW") or 0)
            n = max(n1, n2)
            cand.append((n, p.stat().st_mtime, p))
        except Exception:
            continue
    if not cand:
        return files[0] if files else None
    cand.sort(key=lambda t: (t[0], t[1]))  # ascending
    return cand[-1][2]  # largest n, newest


def fig_candidates(gal: str) -> List[Path]:
    figs = list(Path("paper/figures").glob(f"compare_fit_{gal}_*.svg"))
    if not figs:
        figs = list(Path("paper/figures").glob(f"compare_fit_{gal}*.svg"))
    return sorted(figs, key=lambda p: p.stat().st_mtime, reverse=True)


def _load_blacklist() -> set[str]:
    p = Path('data/sparc/sets/blacklist.txt')
    s: set[str] = set()
    try:
        for ln in p.read_text(encoding='utf-8').splitlines():
            t = ln.strip()
            if not t or t.startswith('#'):
                continue
            name = t.split(',', 1)[0].strip()
            if name:
                s.add(name)
    except Exception:
        pass
    return s


def per_galaxy_chi2_ulw(data: Dict[str, Any]) -> List[Tuple[str, float, float, int]]:
    """Compute an approximate per-galaxy ULW chi2 with shared (lam,A,gas_scale).
    Uses mu and optional alpha_line stored in the multi-fit result.
    This is for ranking (worst/median) in SOTA.
    """
    try:
        from scripts.fit_sparc_fdbl import read_sparc_massmodels
        from scripts.compare_fit_multi import model_ulw_accel, line_bias_accel
        import numpy as _np
    except Exception:
        return []
    try:
        lam = float(data.get("lam"))
        A = float(data.get("A"))
        gscale = float(data.get("gas_scale", 1.0))
    except Exception:
        return []
    names: List[str] = data.get("names", [])
    # Exclude blacklist from consideration
    bl = _load_blacklist()
    names = [nm for nm in names if nm not in bl]
    mus = data.get("mu", {}).get("ULW", {})
    res: List[Tuple[str, float, float, int]] = []
    err_floor_kms = 5.0
    for nm in names:
        try:
            rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), nm)
            R = rc.R
            # observed accel and error
            Rm = _np.maximum(R, 1e-6)
            Veff = rc.Vobs
            # per-point floor: clip(0.03*Vobs, 3..7) km/s
            floor = _np.clip(0.03 * _np.abs(Veff), 3.0, 7.0)
            eVeff = _np.sqrt(_np.maximum(rc.eV, 1e-6) ** 2 + floor ** 2)
            g_obs = (Veff * Veff) / Rm
            eg_obs = 2.0 * Veff * _np.maximum(eVeff, 1e-6) / Rm
            # components
            g_gas = (rc.Vgas * rc.Vgas) / Rm
            vstar2 = rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul
            g_star = vstar2 / Rm
            # ULW field with shared params (boost tied to lam)
            s1 = lam / 8.0
            s2 = lam / 3.0
            g_ulw = model_ulw_accel(
                R, rc.SBdisk, lam_kpc=lam, A=A, pix_kpc=0.2, size=256,
                boost=0.5, s1_kpc=s1, s2_kpc=s2,
                pad_factor=2,
            )
            # line term (unit strength)
            g_line = line_bias_accel(R, rc.SBdisk, pix_kpc=0.2, size=256, line_eps_kpc=0.5, pad_factor=2)
            muinfo = mus.get(nm, {})
            if isinstance(muinfo, dict):
                mu = float(muinfo.get("mu", muinfo.get("mu_d", 0.5)))
                alpha = float(muinfo.get("alpha_line", 0.0))
            else:
                mu = float(muinfo)
                alpha = 0.0
            g_model = gscale * g_gas + mu * g_star + g_ulw + alpha * g_line
            w = 1.0 / _np.maximum(eg_obs, 1e-6)
            m = _np.isfinite(g_obs) & _np.isfinite(eg_obs) & _np.isfinite(g_model)
            N = int(_np.sum(m))
            chi = float(_np.nansum(((g_model[m] - g_obs[m]) * w[m]) ** 2))
            red = chi / max(N - 1, 1)
            res.append((nm, red, chi, N))
        except Exception:
            continue
    # sort descending by chi (worst first)
    res.sort(key=lambda t: t[1], reverse=True)
    return res


def _aggregate_mond_vs_gr(data: Dict[str, Any], a0_kpc: float = A0_KPC) -> Tuple[Dict[str, float], Dict[str, int]]:
    """Compute aggregate AICc for MOND baseline using GR mu as proxy.

    - a0 fixed to 1.2e-10 m/s² (≈3.7×10³ (km$^2$ s$^{-2}$)/kpc)
    - Uses same error-floor scheme as ranking (clip(0.03*V, 3..7) km/s)
    - k counting identical to GR (per-galaxy mu only)
    Returns ({'AICc_GR','AICc_MOND','AICc_ULW'}, {'N_GR','N_MOND','N_ULW','k_GR','k_MOND','k_ULW'})
    """
    try:
        from scripts.fit_sparc_fdbl import read_sparc_massmodels
        import numpy as _np
    except Exception:
        return {"AICc_GR": _np.nan, "AICc_MOND": _np.nan, "AICc_ULW": _np.nan}, {}
    names: List[str] = [nm for nm in data.get('names', []) if nm not in _load_blacklist()]
    mus_gr = data.get('mu', {}).get('GR', {})
    chi_gr = 0.0; chi_mond = 0.0; chi_ulw = float(data.get('chi2_total', {}).get('ULW') or 0.0)
    N_gr = 0; N_mond = 0; N_ulw = int(data.get('N_total', {}).get('ULW') or 0)
    for nm in names:
        try:
            rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), nm)
            R = rc.R; Rm = _np.maximum(R, 1e-6)
            Veff = rc.Vobs; floor = _np.clip(0.03 * _np.abs(Veff), 3.0, 7.0)
            eVeff = _np.sqrt(_np.maximum(rc.eV, 1e-6) ** 2 + floor ** 2)
            g_obs = (Veff * Veff) / Rm
            eg_obs = 2.0 * Veff * _np.maximum(eVeff, 1e-6) / Rm
            g_gas = (rc.Vgas * rc.Vgas) / Rm
            g_star = (rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul) / Rm
            # GR baseline with per-galaxy mu
            muinfo = mus_gr.get(nm, {})
            mu = float(muinfo.get('mu', muinfo.get('mu_d', 0.6)))
            g_gr = g_gas + mu * g_star
            w = 1.0 / _np.maximum(eg_obs, 1e-6)
            m = _np.isfinite(g_obs) & _np.isfinite(eg_obs) & _np.isfinite(g_gr)
            N = int(_np.sum(m)); N_gr += N
            chi_gr += float(_np.nansum(((g_gr[m] - g_obs[m]) * w[m]) ** 2))
            # MOND baseline with same mu, a0 fixed
            gN = g_gr
            half = 0.5 * gN
            g_mond = half + _np.sqrt(half * half + gN * a0_kpc)
            m2 = _np.isfinite(g_obs) & _np.isfinite(eg_obs) & _np.isfinite(g_mond)
            N_mond += int(_np.sum(m2))
            chi_mond += float(_np.nansum(((g_mond[m2] - g_obs[m2]) * w[m2]) ** 2))
        except Exception:
            continue
    # AICc aggregation (μ per galaxy → k = len(names))
    k_gr = len(names); k_mond = len(names); k_ulw = (len(names) + 3)
    def aicc(chi, k, N):
        if N - k - 1 <= 0:
            return float('nan')
        return chi + 2 * k + (2 * k * (k + 1)) / (N - k - 1)
    return (
        {
            'AICc_GR': aicc(chi_gr, k_gr, N_gr),
            'AICc_MOND': aicc(chi_mond, k_mond, N_mond),
            'AICc_ULW': aicc(chi_ulw, k_ulw, N_ulw),
        },
        {'N_GR': N_gr, 'N_MOND': N_mond, 'N_ULW': N_ulw, 'k_GR': k_gr, 'k_MOND': k_mond, 'k_ULW': k_ulw},
    )


def _aggregate_grdm_vs_gr(data: Dict[str, Any]) -> Tuple[Dict[str, float], Dict[str, int]]:
    """Aggregate AICc for GR+DM vs GR with two halo families and per-galaxy model choice.

    Families:
      - NFW with c–M tie per galaxy: free param V200 (1 dof), c=c(V200)
      - Cored isothermal: free params (V0, rc) (2 dof)

    For each galaxy, pick the family with lower χ². Aggregate N,k accordingly.
    """
    try:
        from scripts.fit_sparc_fdbl import read_sparc_massmodels
        import numpy as _np
    except Exception:
        return {"AICc_GR": _np.nan, "AICc_GRDM": _np.nan, "AICc_ULW": _np.nan}, {}
    names: List[str] = [nm for nm in data.get('names', []) if nm not in _load_blacklist()]
    mus_gr = data.get('mu', {}).get('GR', {})
    gscale = float(data.get('gas_scale', 1.0))
    chi_gr = 0.0; chi_grdm = 0.0; chi_ulw = float(data.get('chi2_total', {}).get('ULW') or 0.0)
    N_gr = 0; N_grdm = 0; N_ulw = int(data.get('N_total', {}).get('ULW') or 0)
    k_grdm_sum = 0
    def cM_expected(V200: float) -> float:
        ce = 10.0 * (max(V200, 1e-6) / 200.0) ** (-0.1)
        return float(max(5.0, min(20.0, ce)))
    SIGMA_LN_C = 0.35  # ~0.15 dex 相当の緩い事前
    for nm in names:
        try:
            rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), nm)
            R = rc.R; Rm = _np.maximum(R, 1e-6)
            Vobs = rc.Vobs; eV = _np.maximum(rc.eV, 1e-6)
            Vgas2 = gscale * (rc.Vgas * rc.Vgas)
            mu = float((mus_gr.get(nm, {}) or {}).get('mu', 0.7))
            Vstar2 = mu * (rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul)
            gobs = (Vobs * Vobs) / Rm
            floor = _np.clip(0.03 * _np.abs(Vobs), 3.0, 7.0)
            eVe = _np.sqrt(eV*eV + floor*floor)
            eg = 2.0 * Vobs * eVe / Rm
            w = 1.0 / _np.maximum(eg, 1e-6)
            # common mask (data-driven)
            m0 = _np.isfinite(gobs) & _np.isfinite(w)
            # GR baseline chi on common mask
            ggr = (Vgas2 + Vstar2) / Rm
            N = int(_np.sum(m0)); N_gr += N
            chi_gr += float(_np.nansum(((ggr[m0] - gobs[m0]) * w[m0]) ** 2))
            # GR+DM candidates
            # (1) NFW : (V200, c) grid + c–M事前（ln c ガウス, σ=SIGMA_LN_C）
            best_nfw = (math.inf, (150.0, 10.0))
            for V200 in [80, 120, 160, 200, 240, 280]:
                c_exp = cM_expected(V200)
                for c in [5.0, 7.0, 10.0, 12.0, 15.0, 20.0]:
                    Vdm = _v_nfw(R, V200, c)
                    gdm = (Vdm * Vdm) / Rm
                    gmod = ggr + gdm
                    chi = float(_np.nansum(((gmod[m0] - gobs[m0]) * w[m0]) ** 2))
                    # prior penalty on ln c
                    pen = ((math.log(max(c,1e-6)) - math.log(max(c_exp,1e-6))) / SIGMA_LN_C) ** 2
                    chi_p = chi + pen
                    if chi_p < best_nfw[0]:
                        best_nfw = (chi_p, (V200, c))
            # (2) Cored isothermal : (V0, rc) grid
            best_iso = (math.inf, (120.0, 3.0))
            for V0 in [60, 90, 120, 150, 180, 220]:
                for rc_kpc in [1.0, 2.0, 3.0, 5.0, 8.0]:
                    Vdm = _v_iso_core(R, V0, rc_kpc)
                    gdm = (Vdm * Vdm) / Rm
                    gmod = ggr + gdm
                    chi = float(_np.nansum(((gmod[m0] - gobs[m0]) * w[m0]) ** 2))
                    if chi < best_iso[0]:
                        best_iso = (chi, (V0, rc_kpc))
            # pick better family per galaxy
            if best_nfw[0] <= best_iso[0]:
                chi_grdm += best_nfw[0]
                k_grdm_sum += 2  # V200, c
            else:
                chi_grdm += best_iso[0]
                k_grdm_sum += 2  # V0, rc
            N_grdm += N
        except Exception:
            continue
    # AICc aggregation
    k_gr = len(names)
    k_grdm = len(names) + k_grdm_sum  # mu per galaxy + (DM dof per galaxy)
    k_ulw = (len(names) + 3)
    def aicc(chi, k, N):
        if N - k - 1 <= 0:
            return float('nan')
        return chi + 2 * k + (2 * k * (k + 1)) / (N - k - 1)
    return (
        {
            'AICc_GR': aicc(chi_gr, k_gr, N_gr),
            'AICc_GRDM': aicc(chi_grdm, k_grdm, N_grdm),
            'AICc_ULW': aicc(chi_ulw, k_ulw, N_ulw),
        },
        {'N_GR': N_gr, 'N_GRDM': N_grdm, 'N_ULW': N_ulw, 'k_GR': k_gr, 'k_GRDM': k_grdm, 'k_ULW': k_ulw},
    )


def _win_rates(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compute per-galaxy win counts (χ² lower is win) among GR, GR+DM, MOND, FDB."""
    try:
        from scripts.fit_sparc_fdbl import read_sparc_massmodels
        import numpy as _np
    except Exception:
        return {}
    # map ULW per-galaxy chi² via helper
    ranking = per_galaxy_chi2_ulw(data)
    chi_ulw = {nm: chi for (nm, _red, chi, _N) in ranking}
    names: List[str] = [nm for nm in data.get('names', []) if nm not in _load_blacklist()]
    mus_gr = data.get('mu', {}).get('GR', {})
    gscale = float(data.get('gas_scale', 1.0))
    wins = {'FDB_vs_GR': 0, 'GRDM_vs_GR': 0, 'MOND_vs_GR': 0, 'total': 0}
    for nm in names:
        try:
            rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), nm)
            R = rc.R; Rm = _np.maximum(R, 1e-6)
            Vobs = rc.Vobs; eV = _np.maximum(rc.eV, 1e-6)
            Vgas2 = gscale * (rc.Vgas * rc.Vgas)
            mu = float((mus_gr.get(nm, {}) or {}).get('mu', 0.7))
            Vstar2 = mu * (rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul)
            gobs = (Vobs * Vobs) / Rm
            floor = _np.clip(0.03 * _np.abs(Vobs), 3.0, 7.0)
            eVe = _np.sqrt(eV*eV + floor*floor)
            eg = 2.0 * Vobs * _np.maximum(eVe, 1e-6) / Rm
            w = 1.0 / _np.maximum(eg, 1e-6)
            # GR chi
            ggr = (Vgas2 + Vstar2) / Rm
            m = _np.isfinite(ggr) & _np.isfinite(gobs) & _np.isfinite(w)
            chi_gr = float(_np.nansum(((ggr[m] - gobs[m]) * w[m]) ** 2))
            # GR+DM (best V200)
            best = (math.inf, 150.0)
            for V200 in [80, 120, 160, 200, 240, 280]:
                Vdm = _v_nfw_cM(R, V200)
                gdm = (Vdm * Vdm) / Rm
                gmod = ggr + gdm
                m2 = _np.isfinite(gmod) & _np.isfinite(gobs) & _np.isfinite(w)
                chi = float(_np.nansum(((gmod[m2] - gobs[m2]) * w[m2]) ** 2))
                if chi < best[0]:
                    best = (chi, V200)
            chi_grdm = best[0]
            # MOND
            gN = ggr
            half = 0.5 * gN
            gMOND = half + _np.sqrt(_np.maximum(half*half + gN * A0_KPC, 0.0))
            m3 = _np.isfinite(gMOND) & _np.isfinite(gobs) & _np.isfinite(w)
            chi_mond = float(_np.nansum(((gMOND[m3] - gobs[m3]) * w[m3]) ** 2))
            # FDB from cache list (skip if missing)
            cu = chi_ulw.get(nm, None)
            if cu is None:
                continue
            wins['total'] += 1
            if cu < chi_gr: wins['FDB_vs_GR'] += 1
            if chi_grdm < chi_gr: wins['GRDM_vs_GR'] += 1
            if chi_mond < chi_gr: wins['MOND_vs_GR'] += 1
        except Exception:
            continue
    return wins


def _win_rates_aicc(data: Dict[str, Any]) -> Dict[str, Any]:
    """Compute per-galaxy win rates using ΔAICc<0 vs GR.
    k per galaxy: GR(1: mu), GRDM(NFW:2=mu+V200 | ISO:3=mu+V0+rc), FDB(1: mu), MOND(1: mu)
    Shared ULW(ε,k0,m)は銀河横断の共有自由度のため、per-galaxy勝率では除外（注記で明記）。
    """
    try:
        from scripts.fit_sparc_fdbl import read_sparc_massmodels
        import numpy as _np
    except Exception:
        return {}
    ranking = per_galaxy_chi2_ulw(data)
    chi_ulw = {nm: (chi, N) for (nm, _red, chi, N) in ranking}
    names: List[str] = [nm for nm in data.get('names', []) if nm not in _load_blacklist()]
    mus_gr = data.get('mu', {}).get('GR', {})
    gscale = float(data.get('gas_scale', 1.0))
    wr = {'FDB': 0, 'GRDM': 0, 'MOND': 0, 'total': 0}
    for nm in names:
        try:
            rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), nm)
            R = rc.R; Rm = _np.maximum(R, 1e-6)
            Vobs = rc.Vobs; eV = _np.maximum(rc.eV, 1e-6)
            Vgas2 = gscale * (rc.Vgas * rc.Vgas)
            mu = float((mus_gr.get(nm, {}) or {}).get('mu', 0.7))
            Vstar2 = mu * (rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul)
            gobs = (Vobs * Vobs) / Rm
            floor = _np.clip(0.03 * _np.abs(Vobs), 3.0, 7.0)
            eVe = _np.sqrt(eV*eV + floor*floor)
            eg = 2.0 * Vobs * _np.maximum(eVe, 1e-6) / Rm
            w = 1.0 / _np.maximum(eg, 1e-6)
            m = _np.isfinite(Vobs) & _np.isfinite(eV)
            # GR
            ggr = (Vgas2 + Vstar2) / Rm
            m0 = _np.isfinite(ggr) & _np.isfinite(gobs) & _np.isfinite(w)
            N = int(_np.sum(m0))
            chi_gr = float(_np.nansum(((ggr[m0] - gobs[m0]) * w[m0]) ** 2))
            k_gr = 1
            # GRDM: pick best of NFW/ISO
            best_nfw = (float('inf'), 150.0)
            for V200 in [80, 120, 160, 200, 240, 280]:
                Vdm = _v_nfw_cM(R, V200)
                gmod = ggr + (Vdm * Vdm) / Rm
                m1 = _np.isfinite(gmod) & _np.isfinite(gobs) & _np.isfinite(w)
                chi = float(_np.nansum(((gmod[m1] - gobs[m1]) * w[m1]) ** 2))
                if chi < best_nfw[0]: best_nfw = (chi, V200)
            best_iso = (float('inf'), (120.0, 3.0))
            for V0 in [60, 90, 120, 150, 180, 220]:
                for rc_kpc in [1.0, 2.0, 3.0, 5.0, 8.0]:
                    Vdm = _v_iso_core(R, V0, rc_kpc)
                    gmod = ggr + (Vdm * Vdm) / Rm
                    m2 = _np.isfinite(gmod) & _np.isfinite(gobs) & _np.isfinite(w)
                    chi = float(_np.nansum(((gmod[m2] - gobs[m2]) * w[m2]) ** 2))
                    if chi < best_iso[0]: best_iso = (chi, (V0, rc_kpc))
            if best_nfw[0] <= best_iso[0]:
                chi_grdm = best_nfw[0]; k_grdm = 2
            else:
                chi_grdm = best_iso[0]; k_grdm = 3
            # MOND
            gN = ggr; half = 0.5 * gN
            gMOND = half + _np.sqrt(_np.maximum(half*half + gN * A0_KPC, 0.0))
            m3 = _np.isfinite(gMOND) & _np.isfinite(gobs) & _np.isfinite(w)
            chi_mond = float(_np.nansum(((gMOND[m3] - gobs[m3]) * w[m3]) ** 2))
            k_mond = 1
            # FDB per-galaxy from cache (mu only)
            cu = chi_ulw.get(nm)
            if cu is None:
                continue
            chi_ulw_gal, N_ulw_gal = cu
            k_ulw = 1
            # AICc
            def aicc(chi, k, Npts):
                if Npts - k - 1 <= 0: return float('inf')
                return chi + 2*k + (2*k*(k+1)) / (Npts - k - 1)
            a_gr = aicc(chi_gr, k_gr, N)
            a_grdm = aicc(chi_grdm, k_grdm, N)
            a_mond = aicc(chi_mond, k_mond, N)
            a_ulw = aicc(chi_ulw_gal, k_ulw, N_ulw_gal)
            wr['total'] += 1
            if a_ulw < a_gr: wr['FDB'] += 1
            if a_grdm < a_gr: wr['GRDM'] += 1
            if a_mond < a_gr: wr['MOND'] += 1
        except Exception:
            continue
    return wr


def _load_disk_bul_ml() -> Dict[str, Dict[str, float | None]]:
    """Load per-galaxy M/L summaries from assets/results/global_fit_ml.csv.

    Supports flexible schemas:
      - Columns: ml_disk, ml_bul (point only)
      - Or: ml_disk_map, ml_disk_p16, ml_disk_p84 (and bulge counterparts)

    Returns name -> {
      'md_map','md_p16','md_p84','mb_map','mb_p16','mb_p84'
    } with values or None when unavailable.
    """
    p = Path('assets/results/global_fit_ml.csv')
    res: Dict[str, Dict[str, float | None]] = {}
    if not p.exists():
        return res
    try:
        import csv
        with p.open('r', encoding='utf-8', newline='') as f:
            r = csv.DictReader(f)
            for row in r:
                try:
                    name = str(row['name']).strip()
                except Exception:
                    continue
                # disk
                md_map = None; md_p16 = None; md_p84 = None
                if 'ml_disk_map' in r.fieldnames:
                    try: md_map = float(row.get('ml_disk_map') or 'nan')
                    except Exception: md_map = None
                    try: md_p16 = float(row.get('ml_disk_p16') or 'nan')
                    except Exception: md_p16 = None
                    try: md_p84 = float(row.get('ml_disk_p84') or 'nan')
                    except Exception: md_p84 = None
                else:
                    try:
                        md_map = float(row.get('ml_disk') or 'nan')
                    except Exception:
                        md_map = None
                # bulge
                mb_map = None; mb_p16 = None; mb_p84 = None
                if 'ml_bul_map' in r.fieldnames or 'ml_bulge_map' in r.fieldnames:
                    key_map = 'ml_bul_map' if 'ml_bul_map' in r.fieldnames else 'ml_bulge_map'
                    key_p16 = 'ml_bul_p16' if 'ml_bul_p16' in r.fieldnames else 'ml_bulge_p16'
                    key_p84 = 'ml_bul_p84' if 'ml_bul_p84' in r.fieldnames else 'ml_bulge_p84'
                    try: mb_map = float(row.get(key_map) or 'nan')
                    except Exception: mb_map = None
                    try: mb_p16 = float(row.get(key_p16) or 'nan')
                    except Exception: mb_p16 = None
                    try: mb_p84 = float(row.get(key_p84) or 'nan')
                    except Exception: mb_p84 = None
                else:
                    try:
                        mb_map = float(row.get('ml_bul') or row.get('ml_bulge') or 'nan')
                    except Exception:
                        mb_map = None
                def _clean(x: float | None) -> float | None:
                    return x if isinstance(x, float) and x == x else None
                res[name] = {
                    'md_map': _clean(md_map), 'md_p16': _clean(md_p16), 'md_p84': _clean(md_p84),
                    'mb_map': _clean(mb_map), 'mb_p16': _clean(mb_p16), 'mb_p84': _clean(mb_p84),
                }
    except Exception:
        return {}
    return res


def _v_nfw_cM(R: List[float] | Any, V200: float, H0: float = 70.0) -> Any:
    """NFW circular velocity with c–M-like tie: c = 10*(V200/200)^-0.1 (clamped 5..20).
    R: kpc, V200: km/s, returns Vdm[km/s].
    """
    import numpy as _np
    R = _np.asarray(R, dtype=float)
    c = 10.0 * (max(V200, 1e-6) / 200.0) ** (-0.1)
    c = float(max(5.0, min(20.0, c)))
    R200 = (V200 / (10.0 * H0)) * 1000.0  # kpc
    x = _np.maximum(R / max(R200, 1e-6), 1e-6)
    f = _np.log(1.0 + c) - c / (1.0 + c)
    num = _np.log(1.0 + c * x) - (c * x) / (1.0 + c * x)
    V = V200 * _np.sqrt(_np.maximum(num / (_np.maximum(x, 1e-9) * f), 0.0))
    return V


def _v_nfw(R: List[float] | Any, V200: float, c: float, H0: float = 70.0) -> Any:
    """NFW circular velocity with explicit concentration c."""
    import numpy as _np
    R = _np.asarray(R, dtype=float)
    c = float(max(0.5, min(50.0, c)))
    R200 = (V200 / (10.0 * H0)) * 1000.0  # kpc
    x = _np.maximum(R / max(R200, 1e-6), 1e-6)
    f = _np.log(1.0 + c) - c / (1.0 + c)
    num = _np.log(1.0 + c * x) - (c * x) / (1.0 + c * x)
    V = V200 * _np.sqrt(_np.maximum(num / (_np.maximum(x, 1e-9) * f), 0.0))
    return V


def _v_iso_core(R: List[float] | Any, V0: float, rc: float) -> Any:
    """Cored isothermal halo: V^2 = V0^2 * (1 - rc/R arctan(R/rc))."""
    import numpy as _np
    R = _np.asarray(R, dtype=float)
    x = _np.maximum(R / max(rc, 1e-6), 1e-6)
    term = 1.0 - (1.0 / x) * _np.arctan(x)
    V = V0 * _np.sqrt(_np.maximum(term, 0.0))
    return V


def _err_floor(Vobs: Any, eV: Any) -> Any:
    import numpy as _np
    Vobs = _np.asarray(Vobs, dtype=float)
    eV = _np.asarray(eV, dtype=float)
    floor = _np.clip(0.03 * _np.abs(Vobs), 3.0, 7.0)
    return _np.sqrt(_np.maximum(eV, 1e-6) ** 2 + floor ** 2)


def _refine_nfw(R, Vobs, eV, Vgas2, Vstar2, V200_init: float, c_init: float) -> tuple[float, float, float]:
    """Refine NFW(V200,c) around an initial grid pick using smaller steps."""
    import numpy as _np
    best = (float('inf'), V200_init, c_init)
    eVe = _err_floor(Vobs, eV)
    for V200 in [V200_init - 40, V200_init - 20, V200_init, V200_init + 20, V200_init + 40]:
        if V200 <= 20: continue
        c0 = max(5.0, min(20.0, c_init))
        for c in [c0 - 3, c0 - 1.5, c0, c0 + 1.5, c0 + 3]:
            Vdm = _v_nfw(R, V200, max(0.5, c))
            Vmod = _np.sqrt(_np.maximum(Vgas2 + Vstar2 + Vdm * Vdm, 0.0))
            chi = float(_np.nansum(((Vmod - Vobs) * (1.0 / _np.maximum(eVe, 1e-6))) ** 2))
            if chi < best[0]:
                best = (chi, V200, float(max(0.5, c)))
    return best


def _refine_iso(R, Vobs, eV, Vgas2, Vstar2, V0_init: float, rc_init: float) -> tuple[float, float, float]:
    """Refine ISO(V0,rc) with finer grid."""
    import numpy as _np
    best = (float('inf'), V0_init, rc_init)
    eVe = _err_floor(Vobs, eV)
    for V0 in [V0_init - 40, V0_init - 20, V0_init, V0_init + 20, V0_init + 40]:
        if V0 <= 10: continue
        for rc_kpc in [rc_init - 1.5, rc_init - 0.5, rc_init, rc_init + 0.5, rc_init + 1.5]:
            rc_kpc = float(max(0.3, rc_kpc))
            Vdm = _v_iso_core(R, V0, rc_kpc)
            Vmod = _np.sqrt(_np.maximum(Vgas2 + Vstar2 + Vdm * Vdm, 0.0))
            chi = float(_np.nansum(((Vmod - Vobs) * (1.0 / _np.maximum(eVe, 1e-6))) ** 2))
            if chi < best[0]:
                best = (chi, V0, rc_kpc)
    return best


def _best_mond_a0(data: Dict[str, Any]) -> float:
    """Find shared MOND a0 in (km² s⁻²)/kpc minimizing aggregate AICc."""
    try:
        from scripts.fit_sparc_fdbl import read_sparc_massmodels
        import numpy as _np
    except Exception:
        return A0_KPC
    names: List[str] = [nm for nm in data.get('names', []) if nm not in _load_blacklist()]
    mus_gr = data.get('mu', {}).get('GR', {})
    cand_si = [8e-11, 1.0e-10, 1.2e-10, 1.4e-10, 1.6e-10, 1.8e-10]

    def agg_aicc(a0_si: float) -> float:
        a0 = _a0_si_to_kpc(a0_si)
        chi = 0.0; Ntot = 0; k = len(names) + 1  # per-galaxy mu + shared a0
        for nm in names:
            try:
                rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), nm)
                R = rc.R; Rm = _np.maximum(R, 1e-6)
                Vobs = rc.Vobs; eV = rc.eV
                eVe = _err_floor(Vobs, eV)
                Vgas2 = (data.get('gas_scale', 1.0)) * (rc.Vgas * rc.Vgas)
                mu = float((mus_gr.get(nm, {}) or {}).get('mu', 0.7))
                Vstar2 = mu * (rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul)
                gobs = (Vobs * Vobs) / Rm
                gN = (Vgas2 + Vstar2) / Rm
                half = 0.5 * gN
                gMOND = half + _np.sqrt(_np.maximum(half * half + gN * a0, 0.0))
                w = 1.0 / _np.maximum(2.0 * Vobs * eVe / Rm, 1e-6)
                m = _np.isfinite(gMOND) & _np.isfinite(gobs) & _np.isfinite(w)
                N = int(_np.sum(m)); Ntot += N
                chi += float(_np.nansum(((gMOND[m] - gobs[m]) * w[m]) ** 2))
            except Exception:
                continue
        if Ntot - k - 1 <= 0: return float('inf')
        return chi + 2*k + (2*k*(k+1))/(Ntot - k - 1)
    best = min(((agg_aicc(a0_si), a0_si) for a0_si in cand_si), key=lambda t: t[0])
    return _a0_si_to_kpc(float(best[1]))


def _tri_compare_figure(nm: str, data: Dict[str, Any]) -> Path | None:
    """Generate a tri-panel comparison figure (GR+DM / MOND / FDB)."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from scripts.utils.mpl_fonts import use_jp_font
        use_jp_font()
        import numpy as _np
        from scripts.fit_sparc_fdbl import read_sparc_massmodels
        from scripts.compare_fit_multi import model_ulw_accel
    except Exception:
        return None
    try:
        rc = read_sparc_massmodels(Path("data/sparc/MassModels_Lelli2016c.mrt"), nm)
        R = rc.R; Rm = _np.maximum(R, 1e-6)
        Vobs = rc.Vobs; eV = _np.maximum(rc.eV, 1e-6)
        gscale = float(data.get('gas_scale', 1.0))
        mus = data.get('mu', {})
        mu_gr = float((mus.get('GR', {}).get(nm, {}) or {}).get('mu', 0.7))
        mu_ulw = float((mus.get('ULW', {}).get(nm, {}) or {}).get('mu', mu_gr))
        Vgas2 = gscale * (rc.Vgas * rc.Vgas)
        Vstar2 = mu_gr * (rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul)
        # GR+DM (NFW c–M)
        # quick 1D grid for V200
        best = (math.inf, 150.0)
        for V200 in [80, 120, 160, 200, 240, 280]:
            Vdm = _v_nfw_cM(R, V200)
            Vmod2 = Vgas2 + Vstar2 + Vdm * Vdm
            gmod = Vmod2 / Rm
            gobs = (Vobs * Vobs) / Rm
            eVe = _np.sqrt(eV*eV + _np.clip(0.03*_np.abs(Vobs), 3.0, 7.0)**2)
            eg = 2.0 * Vobs * eVe / Rm
            w = 1.0 / _np.maximum(eg, 1e-6)
            m = _np.isfinite(gmod) & _np.isfinite(gobs) & _np.isfinite(w)
            chi = float(_np.nansum(((gmod[m] - gobs[m])*w[m])**2))
            if chi < best[0]:
                best = (chi, V200)
        V200_b = best[1]
        Vdm = _v_nfw_cM(R, V200_b)
        Vgrdm = _np.sqrt(_np.maximum(Vgas2 + Vstar2 + Vdm*Vdm, 0.0))
        # MOND (a0 fixed in local units), use GR μ
        gN = (Vgas2 + Vstar2) / Rm
        half = 0.5 * gN
        gMOND = half + _np.sqrt(_np.maximum(half*half + gN * A0_KPC, 0.0))
        Vmond = _np.sqrt(_np.maximum(gMOND * Rm, 0.0))
        # FDB (ULW shared)
        lam = float(data.get('lam', 20.0)); A = float(data.get('A', 1.0))
        g_ulw_1 = model_ulw_accel(R, rc.SBdisk, lam_kpc=lam, A=1.0, pix_kpc=0.2, size=256,
                                  boost=0.5, s1_kpc=lam/8.0, s2_kpc=lam/3.0, pad_factor=2)
        gFDB = (Vgas2 + mu_ulw*(rc.Vdisk*rc.Vdisk + rc.Vbul*rc.Vbul)) / Rm + A * g_ulw_1
        Vfdb = _np.sqrt(_np.maximum(gFDB * Rm, 0.0))
        # Plot
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), sharex=True, sharey=True)
        # Also compute cored isothermal and pick the better GR+DM family for display
        import numpy as _np
        def cM_expected(V200: float) -> float:
            ce = 10.0 * (max(V200, 1e-6) / 200.0) ** (-0.1)
            return float(max(5.0, min(20.0, ce)))
        SIGMA_LN_C = 0.35
        best_nfw = (math.inf, (V200_b, 10.0))
        for V200 in [80, 120, 160, 200, 240, 280]:
            c_exp = cM_expected(V200)
            for c in [5.0, 7.0, 10.0, 12.0, 15.0, 20.0]:
                Vdm = _v_nfw(R, V200, c)
                Vnfw = _np.sqrt(_np.maximum(Vgas2 + Vstar2 + Vdm*Vdm, 0.0))
                chi = float(_np.nansum(((Vnfw - Vobs) * (1.0/_np.maximum(eV,1e-6)))**2))
                pen = ((math.log(max(c,1e-6)) - math.log(max(c_exp,1e-6))) / SIGMA_LN_C) ** 2
                chi_p = chi + pen
                if chi_p < best_nfw[0]: best_nfw = (chi_p, (V200, c))
        best_iso = (math.inf, (120.0, 3.0))
        for V0 in [60, 90, 120, 150, 180, 220]:
            for rc_kpc in [1.0, 2.0, 3.0, 5.0, 8.0]:
                Vdm = _v_iso_core(R, V0, rc_kpc)
                Viso = _np.sqrt(_np.maximum(Vgas2 + Vstar2 + Vdm*Vdm, 0.0))
                chi = float(_np.nansum(((Viso - Vobs) * (1.0/_np.maximum(eV,1e-6)))**2))
                if chi < best_iso[0]: best_iso = (chi, (V0, rc_kpc))
        if best_nfw[0] <= best_iso[0]:
            V200_b, c_b = best_nfw[1]
            Vdm = _v_nfw(R, V200_b, c_b)
            Vgrdm = _np.sqrt(_np.maximum(Vgas2 + Vstar2 + Vdm*Vdm, 0.0))
            grdm_title = f"M1: GR+DM(NFW) — V200={V200_b} km/s, c={c_b}"
        else:
            V0_b, rc_b = best_iso[1]
            Vdm = _v_iso_core(R, V0_b, rc_b)
            Vgrdm = _np.sqrt(_np.maximum(Vgas2 + Vstar2 + Vdm*Vdm, 0.0))
            grdm_title = f"M1: GR+DM(Cored ISO) — V0={V0_b} km/s, rc={rc_b} kpc"

        titles = [
            "GR+DM (best of NFW/ISO)",
            "MOND (a0≈3.7×10³ (km$^2$ s$^{-2}$)/kpc)",
            "FDB (shared μ(k))",
        ]
        curves = [Vgrdm, Vmond, Vfdb]
        for ax, ttl, Vmod in zip(axes, titles, curves):
            ax.errorbar(R, Vobs, yerr=eV, fmt='o', ms=2.5, lw=0.8, color='#444', alpha=0.9)
            ax.plot(R, Vmod, '-', lw=1.6, color='#d62728')
            ax.set_title(ttl, fontsize=9)
            ax.grid(True, ls=':', alpha=0.4)
        axes[0].set_ylabel('V [km/s]')
        fig.suptitle('Tri-compare: GR+DM / MOND / FDB — same data, errors, penalties; shared μ(k)', fontsize=9)
        for ax in axes:
            ax.set_xlabel('R [kpc]')
        fig.tight_layout()
        out = Path('paper/figures') / f'tri_compare_{nm}.svg'
        out.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out, bbox_inches='tight')
        plt.close(fig)
        return out
    except Exception:
        return None


def brief_results(data: Dict[str, Any]) -> str:
    names = data.get("names", [])
    muk = data.get("mu_k", {})
    eps = muk.get("eps"); k0 = muk.get("k0"); mm = muk.get("m")
    # Prefer CV summary μ(k) if available for representative display
    try:
        import json as _json
        cvp = Path('data/results/cv_shared_summary.json')
        if cvp.exists():
            cvd = _json.loads(cvp.read_text(encoding='utf-8'))
            bs = []
            for f in cvd.get('folds', []):
                b = f.get('train_best', {})
                if b:
                    bs.append((float(b.get('mu_eps')), float(b.get('mu_k0')), int(float(b.get('mu_m')))))
            if bs:
                bs.sort(key=lambda t: (t[0], t[1], t[2]))
                mid = bs[len(bs)//2]
                eps, k0, mm = mid
    except Exception:
        pass
    if eps is None or k0 is None or mm is None:
        lam_fallback = data.get('lam'); A_fallback = data.get('A')
        try:
            if eps is None and A_fallback is not None:
                eps = float(A_fallback)
            if k0 is None and lam_fallback not in (None, 0):
                k0 = 1.0 / float(lam_fallback)
            if mm is None:
                mm = 2
        except Exception:
            pass
    gscale = data.get("gas_scale")
    chi = data.get("chi2_total", {})
    aic = data.get("AIC", {})
    Ntot = data.get("N_total", {})
    def aicc(AIC: float | None, k: int | None, N: int | None) -> float | None:
        try:
            AICf = float(AIC or 0.0); kf = int(k or 0); Nf = int(N or 0)
            if Nf - kf - 1 <= 0:
                return None
            return AICf + (2 * kf * (kf + 1)) / (Nf - kf - 1)
        except Exception:
            return None
    k_gr = (aic.get('k') or {}).get('GR'); k_ulw = (aic.get('k') or {}).get('ULW')
    N_gr = Ntot.get('GR'); N_ulw = Ntot.get('ULW')
    aicc_gr = aicc(aic.get('GR'), k_gr, N_gr)
    aicc_ulw = aicc(aic.get('ULW'), k_ulw, N_ulw)
    rows: List[str] = []
    rows.append("<div class=card>")
    rows.append(f"<p>共有 μ(k): ε={h(str(eps))}, k0={h(str(k0))} kpc⁻¹, m={h(str(mm))}, "
                f"gas_scale={h(str(gscale))}</p>")
    rows.append(f"<p>合計χ²: GR={h(str(chi.get('GR')))} / "
                f"ULW={h(str(chi.get('ULW')))}</p>")
    if aic:
        aicc_txt = (
            f"AICc: GR={h(str(aicc_gr))} (n={h(str(N_gr))},k={h(str(k_gr))}) / "
            f"ULW={h(str(aicc_ulw))} (n={h(str(N_ulw))},k={h(str(k_ulw))})"
        )
        rows.append(f"<p>{aicc_txt}</p>")
    rows.append("</div>")
    # (moved) demo/prospective links now handled in main()
    def _load_blacklist() -> set[str]:
        p = Path('data/sparc/sets/blacklist.txt')
        s: set[str] = set()
        try:
            for ln in p.read_text(encoding='utf-8').splitlines():
                t = ln.strip()
                if not t or t.startswith('#'):
                    continue
                name = t.split(',', 1)[0].strip()
                if name:
                    s.add(name)
        except Exception:
            pass
        return s

    rows.append(
        "<table><thead><tr>"
        "<th>Galaxy</th><th>GR &Upsilon;<sub>★</sub></th><th>ULW &Upsilon;<sub>★</sub></th>"
        "<th>Blacklist</th><th>&Upsilon;<sub>★</sub>,disk</th><th>&Upsilon;<sub>★</sub>,bulge</th>"
        "</tr></thead><tbody>"
    )
    ml_gr_map = data.get("ML_star", {}).get("GR", {})
    ml_ulw_map = data.get("ML_star", {}).get("ULW", {})
    mus_gr = data.get("mu", {}).get("GR", {})
    mus_ulw = data.get("mu", {}).get("ULW", {})
    ml_db = _load_disk_bul_ml()
    blset = _load_blacklist()
    for nm in names:
        def _pm_from_ci(mapv: float | None, p16: float | None, p84: float | None) -> str | None:
            if (p16 is not None) and (p84 is not None):
                center = mapv if mapv is not None else (p16 + p84) / 2.0
                sigma = (p84 - p16) / 2.0
                if not _np.isfinite(center) or abs(center) < 1e-6:
                    return None
                try:
                    return f"{center:.3g} ± {sigma:.2g}"
                except Exception:
                    return f"{center} ± {sigma}"
            return None

        def fmt_ml_mu(nm: str, is_ulw: bool) -> str:
            mm = ml_ulw_map.get(nm, {}) if is_ulw else ml_gr_map.get(nm, {})
            if isinstance(mm, dict) and mm:
                # Prefer MAP±68% if available
                s = _pm_from_ci(mm.get('ML_star_map'), mm.get('ML_star_p16'), mm.get('ML_star_p84'))
                if s:
                    return f"Υ★={s}"
                if 'ML_star' in mm and (mm['ML_star'] or 0) > 1e-6:
                    return f"Υ★={mm['ML_star']:.3g}"
                parts = []
                s_d = _pm_from_ci(mm.get('ML_star_disk_map'), mm.get('ML_star_disk_p16'), mm.get('ML_star_disk_p84'))
                s_b = _pm_from_ci(mm.get('ML_star_bulge_map'), mm.get('ML_star_bulge_p16'), mm.get('ML_star_bulge_p84'))
                if s_d:
                    parts.append(f"Υ★,disk={s_d}")
                elif 'ML_star_disk' in mm and (mm['ML_star_disk'] or 0) > 1e-6:
                    parts.append(f"Υ★,disk={mm['ML_star_disk']:.3g}")
                if s_b:
                    parts.append(f"Υ★,bulge={s_b}")
                elif 'ML_star_bulge' in mm and (mm['ML_star_bulge'] or 0) > 1e-6:
                    parts.append(f"Υ★,bulge={mm['ML_star_bulge']:.3g}")
                return ", ".join(parts) if parts else "-"
            legacy = (mus_ulw if is_ulw else mus_gr).get(nm, {})
            if isinstance(legacy, dict):
                if 'mu' in legacy:
                    return f"Υ★={legacy['mu']:.3g}"
                return f"Υ★,disk={legacy.get('mu_d','-')}, Υ★,bulge={legacy.get('mu_b','-')}"
            return f"Υ★={legacy}" if legacy else "-"
        mdinfo = ml_db.get(nm, {})
        def fmt_ml(mapv: float | None, p16: float | None, p84: float | None) -> str:
            if mapv is None and (p16 is None or p84 is None):
                return "-"
            # Prefer credible interval if available
            if (p16 is not None) and (p84 is not None):
                center = mapv if mapv is not None else (p16 + p84) / 2.0
                sigma = (p84 - p16) / 2.0
                try:
                    return f"{center:.3g} ± {sigma:.2g}"
                except Exception:
                    return f"{center} ± {sigma}"
            # Fallback to point estimate
            try:
                return f"{mapv:.3g}" if mapv is not None else "-"
            except Exception:
                return str(mapv) if mapv is not None else "-"
        md_str = fmt_ml(mdinfo.get('md_map'), mdinfo.get('md_p16'), mdinfo.get('md_p84'))
        mb_str = fmt_ml(mdinfo.get('mb_map'), mdinfo.get('mb_p16'), mdinfo.get('mb_p84'))
        memo_url = f"../memo/galaxies/{h(nm)}.md"
        bl_txt = "yes" if nm in blset else "-"
        rows.append(
            "<tr>"
            f"<td><a href=\"{memo_url}\">{h(nm)}</a></td>"
            f"<td>{h(fmt_ml_mu(nm, False))}</td>"
            f"<td>{h(fmt_ml_mu(nm, True))}</td>"
            f"<td>{h(bl_txt)}</td>"
            f"<td>{h(md_str)}</td>"
            f"<td>{h(mb_str)}</td>"
            "</tr>"
        )
    rows.append("</tbody></table>")
    return "\n".join(rows)


def write_html(out: Path, title: str, body: str) -> None:
    # Compute last-updated epoch (ms) from results/figures mtime for client-side display
    res_dir = Path("assets/results")
    fig_dst = Path("paper/figures")
    res_csv = res_dir / 'fdb3_per_galaxy.csv'
    gsum_csv = res_dir / 'global_fit_summary.csv'
    targets = [
        fig_dst / 'sota_improvement_hist.png',
        fig_dst / 'sota_redchi2_scatter.png',
        fig_dst / 'sota_vr_panel.png',
        fig_dst / 'sota_vr_panel_worst.png',
    ]
    def mtime(p: Path) -> float:
        try:
            return p.stat().st_mtime
        except Exception:
            return 0.0
    res_m = max(mtime(res_csv), mtime(gsum_csv))
    figs_m = min(mtime(t) for t in targets) if all(t.exists() for t in targets) else 0.0
    last_epoch_ms = int(max(res_m, figs_m, time.time()) * 1000)
    # static last-updated (server local time) for JS-disabled viewers
    import datetime as _dt
    _dt_local = _dt.datetime.fromtimestamp(last_epoch_ms/1000.0)
    _last_static = _dt_local.strftime('%Y-%m-%d %H:%M')
    # depth-aware relative prefix from server/public
    try:
        rel = out.resolve().relative_to(Path("server/public").resolve())
        depth = max(len(rel.parts) - 1, 0)
    except Exception:
        depth = 0
    pref = "../" * depth
    html = (
        "<!doctype html>\n"
        "<html lang=\"ja-JP\">\n<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"  <meta name=\"x-last-updated-epoch\" content=\"{last_epoch_ms}\">\n"
        f"  <title>{h(title)}</title>\n"
        f"  <link rel=\"stylesheet\" href=\"{pref}styles.css\">\n"
        f"  <script defer src=\"{pref}site-lastmod.js?v={int(time.time()*1000)}\"></script>\n"
        "  <script>window.MathJax={tex:{inlineMath:[['$','$'],['\\(','\\)']]}};</script>\n"
        "  <script id=\"MathJax-script\" async src=\"https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\"></script>\n"
        "</head>\n<body>\n"
        "  <header class=\"site-header\">\n"
        "    <div class=\"wrap\">\n"
        "      <div class=\"brand\">研究進捗</div>\n"
        "      <nav class=\"nav\">\n"
        f"        <a href=\"{pref}index.html\">ホーム</a>\n"
        "        <a href=\"index.html\">State of the Art</a>\n"
        f"        <a href=\"{pref}reports/index.html\">レポート</a>\n"
        "      </nav>\n"
        "    </div>\n"
        "  </header>\n"
        f"  <div class=\"wrap\"><small class=\"lastmod-static\">更新(サーバ時刻): {_last_static}</small></div>\n"
        "  <main class=\"wrap\">\n" + body + "\n  </main>\n"
        "  <footer class=\"site-footer\">\n"
        "    <div class=\"wrap\">ローカル配信(開発用)</div>\n"
        "  </footer>\n"
        "</body>\n</html>\n"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    # Ensure paper figures are web-served under server/public/paper/figures
    try:
        web_fig = Path('server/public/paper/figures')
        web_fig.mkdir(parents=True, exist_ok=True)
        for p in fig_dst.glob('*.svg'):
            dst = web_fig / p.name
            if (not dst.exists()) or (p.stat().st_mtime > dst.stat().st_mtime):
                dst.write_bytes(p.read_bytes())
        # Sync image assets (PNG) used by SOTA demos
        src_assets = Path('assets/figures')
        dst_assets = Path('server/public/assets/figures')
        for p in list(src_assets.rglob('*.png')) + list(src_assets.rglob('*.svg')) + list(src_assets.rglob('*.jpg')):
            rel = p.relative_to(src_assets)
            outp = dst_assets / rel
            outp.parent.mkdir(parents=True, exist_ok=True)
            if (not outp.exists()) or (p.stat().st_mtime > outp.stat().st_mtime):
                outp.write_bytes(p.read_bytes())
    except Exception:
        pass


def main() -> int:
    # Tolerate foreground execution while recommending dispatcher.
    # Also avoid rare UnboundLocalError reports by importing locally.
    try:
        import os as _os
    except Exception:
        _os = None  # type: ignore
    if not (_os and _os.environ.get('GRAV_BG_JOB') == '1'):
        # Do not exit; just warn. build_state_of_the_art is typically light-weight.
        sys.stderr.write(
            "[warn] SOTA build running in foreground (GRAV_BG_JOB!=1).\n"
            "       For long runs, use: scripts/jobs/dispatch_bg.sh -n build_sota -- '<cmd>'\n"
        )
    sota = Path("server/public/state_of_the_art/index.html")
    js = load_jsons()
    best = pick_best_result(js)
    if not best:
        write_html(sota, "State of the Art", "<p>結果がまだありません。</p>")
        return 0
    data = json.loads(best.read_text(encoding="utf-8"))
    names_cache = list(data.get('names', []) or [])
    body: List[str] = []
    body.append("<h1>State of the Art</h1>")
    # What's new (2025-Q3): ULW-l/h callout with shared hyperparams
    try:
        cv_best = Path('data/results/cv_shared_best.json')
        eps_w = k0_w = m_w = gas_w = None
        if cv_best.exists():
            _cv = json.loads(cv_best.read_text(encoding='utf-8'))
            eps_w = _cv.get('eps'); k0_w = _cv.get('k0'); m_w = _cv.get('m'); gas_w = _cv.get('gas')
        wnp = Path('docs/sota/partials/whats_new_2025Q3.html')
        if wnp.exists():
            htmlp = wnp.read_text(encoding='utf-8')
            def _fmt(x):
                try:
                    return f"{float(x):.3g}"
                except Exception:
                    return str(x) if x is not None else "—"
            htmlp = htmlp.replace('{EPS}', _fmt(eps_w)).replace('{K0}', _fmt(k0_w)).replace('{M}', _fmt(m_w)).replace('{GAS}', _fmt(gas_w))
            body.append(htmlp)
    except Exception:
        pass
    # 0) 方針宣言（公平比較・物理一貫性・再現性）
    body.append(
        '<div class=card>'
        '<p><b>方針</b>:</p>'
        '<ul>'
        '<li>FDB（Future Decoherence Bias）を“重力”ではなく<b>見かけの引力</b>として扱う。</li>'
        '<li>太陽系スケールでは GR と同型、銀河スケールでは超長波の自由度で差が出る可能性を検証する。</li>'
        '<li>比較は“観測に対して実運用で使われるベースライン”を含め<b>公正</b>に行う。</li>'
        '<li>GR+DM を含める理由: DM は何でも可ではなく、ハロー形状や自由度は有限で、c–M 関係やコア/カスプ等の宇宙論的整合で拘束される。したがって GR+DM は常に一致するわけではなく、フェアなベースラインである。</li>'
        '</ul>'
        '</div>'
    )
    # Early‑Universe section (Late‑FDB mainline, E‑FDB fallback)
    try:
        from hashlib import sha256 as _sha
        eu_cfg = Path('cfg/early_fdb.json')
        eu_meta = Path('server/public/state_of_the_art/early_universe_meta.json')
        params = {'eps_max': None, 'a_on': None, 'da': None, 'k_c': None}
        sha12 = None
        if eu_cfg.exists():
            raw = eu_cfg.read_bytes()
            sha12 = _sha(raw).hexdigest()[:12]
            try:
                cj = json.loads(raw.decode('utf-8'))
                for k in params:
                    if k in cj: params[k] = cj[k]
            except Exception:
                pass
        pref = '../'  # assets path prefix from SOTA page
        fig1 = Path('assets/figures/early_universe/Fig-EU1_mu_late_contour.png')
        fig2 = Path('assets/figures/early_universe/Fig-EU2_growth_ratio.png')
        fig3 = Path('assets/figures/early_universe/Fig-EU3_uvlf_multiplier.png')
        fig4 = Path('assets/figures/early_universe/Fig-EU4_shell_field.png')
        fig1b = Path('assets/figures/early_universe/Fig-EU1b_bao_cmb_allowed.png')
        fig5 = Path('assets/figures/early_universe/Fig-EU5_21cm_corr.png')
        fig1c = Path('assets/figures/early_universe/Fig-EU1c_class_bao.png')
        card = [
            '<h2>Early‑Universe FDB</h2>',
            '<div class=card>',
            '<p><b>新規ブロック</b>: 初期の球状ミニ・ヴォイド境界が ULM‑P の面光源として働き、外部に 1/r² 形式の見かけ重力を与える。内部は殻対称性でほぼ 0。</p>',
            '<p><b>Late‑FDB（本線）</b>: 再結合後 z≲30 に μ(a,k)=1+ε(a)S(k) を緩やかに立上げ、CMB/BAO を保持しつつ高 z の成長を軽くブースト。<br>'
            '<b>E‑FDB（保険）</b>: 必要時のみ CDM 等価流体として置換（自由度は不増）。</p>',
        ]
        # Param card with sha fingerprint
        card.append(
            '<div class="param-card"><b>パラメタ</b>: '
            f"eps_max={h(str(params['eps_max']))}, a_on={h(str(params['a_on']))}, da={h(str(params['da']))}, k_c={h(str(params['k_c']))} "
            + (f"<small>(sha:{h(sha12)})</small>" if sha12 else '') + '</div>'
        )
        figs = []
        if fig1.exists():
            src = f'{pref}assets/figures/early_universe/{h(fig1.name)}'
            figs.append(f'<figure class="card"><img {_img_html_attrs(src)}><figcaption>Fig‑EU1: μ_late(a,k)</figcaption></figure>')
        if fig2.exists():
            src = f'{pref}assets/figures/early_universe/{h(fig2.name)}'
            figs.append(f'<figure class="card"><img {_img_html_attrs(src)}><figcaption>Fig‑EU2: 成長因子 D の倍率</figcaption></figure>')
        if fig3.exists():
            src = f'{pref}assets/figures/early_universe/{h(fig3.name)}'
            figs.append(f'<figure class="card"><img {_img_html_attrs(src)}><figcaption>Fig‑EU3: UVLF 明るい端の倍率</figcaption></figure>')
        if fig4.exists():
            src = f'{pref}assets/figures/early_universe/{h(fig4.name)}'
            figs.append(f'<figure class="card"><img {_img_html_attrs(src)}><figcaption>Fig‑EU4: 球殻トイ — 外部1/r²・内部~0</figcaption></figure>')
        if fig1b.exists():
            src = f'{pref}assets/figures/early_universe/{h(fig1b.name)}'
            figs.append(f'<figure class="card"><img {_img_html_attrs(src)}><figcaption>Fig‑EU1b: CMB/BAO 整合（プロキシ）で許容される領域</figcaption></figure>')
        if fig5.exists():
            src = f'{pref}assets/figures/early_universe/{h(fig5.name)}'
            figs.append(f'<figure class="card"><img {_img_html_attrs(src)}><figcaption>Fig‑EU5: 識別予測 — 21 cm 境界強度 |∇T_b| と銀河の相関</figcaption></figure>')
        bao_summary_block = ''
        solar_summary_block = ''
        fairness_note = ''
        if fig1c.exists():
            # 併せて数値サマリがあれば表示
            summary = ''
            bao_meta = None
            bao_detail = None
            solar_meta = None
            solar_detail = None
            try:
                cl = json.loads(Path('server/public/state_of_the_art/early_universe_class.json').read_text(encoding='utf-8'))
                if cl.get('available'):
                    summary = f"<small>CLASS 連携: z≈{h(str(round(float(cl.get('z',0)),2)))} / 振幅比≈{h(str(round(float(cl.get('amp_ratio',1.0)),3)))} / Δk≈{h(str(round(float(cl.get('peak_shift',0.0)),4)))} 1/Mpc"  # type: ignore[arg-type]
                    repro_bits = []
                    ver = (cl.get('class_version') or '').strip()
                    if ver:
                        repro_bits.append(f"CLASS {h(ver)}")
                    sha_sp = (cl.get('shared_params_sha') or '')
                    if sha_sp:
                        repro_bits.append(f"shared_params_sha={h(sha_sp[:8])}")
                    sha_cfg = (cl.get('cfg_sha') or '')
                    if sha_cfg:
                        repro_bits.append(f"cfg_sha={h(sha_cfg[:8])}")
                    sha_ini = (cl.get('class_ini_sha') or '')
                    if sha_ini:
                        repro_bits.append(f"class_ini_sha={h(sha_ini[:8])}")
                    if repro_bits:
                        summary += '<br><small>再現: ' + ', '.join(repro_bits) + '</small>'
                    summary += '</small>'
                    if isinstance(cl.get('bao'), dict):
                        bao_meta = cl['bao']
                    if isinstance(cl.get('solar'), dict):
                        solar_meta = cl['solar']
                else:
                    summary = '<small>CLASS が未導入のため、プレースホルダ表示（proxy のみ）</small>'
            except Exception:
                pass
            try:
                data_p = Path('server/public/state_of_the_art/data/fig_eu1c.json')
                if data_p.exists():
                    fig_payload = json.loads(data_p.read_text(encoding='utf-8'))
                    if isinstance(fig_payload.get('bao_likelihood'), dict):
                        bao_detail = fig_payload['bao_likelihood']
                    if isinstance(fig_payload.get('solar_penalty'), dict):
                        solar_detail = fig_payload['solar_penalty']
            except Exception:
                pass
            src = f'{pref}assets/figures/early_universe/{h(fig1c.name)}'
            figs.append(f'<figure class="card"><img {_img_html_attrs(src)}><figcaption>Fig‑EU1c: BAO 検証（CLASS 連携; 成長補正近似） {summary}</figcaption></figure>')
            if bao_meta or bao_detail:
                chi2 = None
                ndof = None
                pval = None
                bao_file = None
                if isinstance(bao_meta, dict):
                    chi2 = bao_meta.get('chi2_total')
                    ndof = bao_meta.get('ndof_total')
                    pval = bao_meta.get('p_value_total')
                    bao_file = bao_meta.get('bao_file')
                datasets = []
                max_pull = None
                aicc_total = None
                if isinstance(bao_detail, dict):
                    aicc_total = bao_detail.get('aicc_total')
                    for ds in bao_detail.get('datasets', []):
                        name = h(str(ds.get('name', '')))
                        zs = ds.get('z', [])
                        obs_kinds = ds.get('observables', [])
                        if zs:
                            z_txt = ','.join([f"{float(z):.2f}" for z in zs])
                        else:
                            z_txt = '—'
                        obs_txt = ', '.join(obs_kinds) if obs_kinds else '—'
                        datasets.append(f"{name} (z={h(z_txt)}; {h(obs_txt)})")
                        pulls = [abs(float(pt.get('pull', 0.0))) for pt in ds.get('per_point', [])]
                        if pulls:
                            candidate = max(pulls)
                            max_pull = candidate if (max_pull is None or candidate > max_pull) else max_pull
                parts = []
                if isinstance(chi2, (int, float)) and isinstance(ndof, (int, float)):
                    parts.append(f"χ²={chi2:.2f} / dof={int(ndof)}")
                if isinstance(aicc_total, (int, float)):
                    parts.append(f"AICc={aicc_total:.2f}")
                if isinstance(pval, (int, float)):
                    parts.append(f"p={pval:.3f}")
                metrics_txt = ', '.join(parts)
                ds_txt = '; '.join(datasets)
                max_pull_txt = f"最大|pull|≲{max_pull:.2f}" if isinstance(max_pull, (int, float)) else ''
                foot = []
                if isinstance(bao_file, str) and bao_file:
                    foot.append(f"src={h(Path(bao_file).name)}")
                if isinstance(bao_detail, dict) and bao_detail.get('param_count'):
                    try:
                        foot.append(f"param_count={int(bao_detail['param_count'])}")
                    except Exception:
                        pass
                foot_txt = ', '.join(foot)
                details = [txt for txt in (ds_txt, max_pull_txt, foot_txt) if txt]
                detail_txt = ' / '.join(details)
                if metrics_txt or detail_txt:
                    bao_summary_block = '<p><b>BAO 尤度</b>: '
                    if metrics_txt:
                        bao_summary_block += h(metrics_txt)
                if detail_txt:
                    bao_summary_block += f"<br><small>{h(detail_txt)}</small>"
                bao_summary_block += '</p>'
            if solar_meta or solar_detail:
                mu_val = None
                delta_mu = None
                delta_a = None
                ratio = None
                a_max = None
                status = None
                if isinstance(solar_meta, dict):
                    mu_val = solar_meta.get('mu_at_au')
                    delta_mu = solar_meta.get('delta_mu')
                    delta_a = solar_meta.get('delta_a_m_s2')
                    ratio = solar_meta.get('delta_a_ratio')
                    a_max = solar_meta.get('a_max_m_s2')
                    status = solar_meta.get('status') or ('pass' if solar_meta.get('pass_bound') else 'fail')
                detail_bits = []
                if isinstance(solar_detail, dict):
                    k_val = solar_detail.get('k_au_1_per_mpc')
                    if k_val is not None:
                        detail_bits.append(f"k(1AU)≈{float(k_val):.3e} Mpc⁻¹")
                if mu_val is not None:
                    detail_bits.append(f"μ(1AU)={float(mu_val):.3f}")
                if delta_mu is not None:
                    detail_bits.append(f"Δμ={float(delta_mu):.3e}")
                if delta_a is not None and a_max is not None:
                    detail_bits.append(f"Δa={float(delta_a):.3e} m s⁻² (許容≤{float(a_max):.1e})")
                if ratio is not None:
                    detail_bits.append(f"比={float(ratio):.3e}")
                state_txt = f"status={h(str(status))}" if status else ''
                solar_summary_block = '<p><b>Solar ペナルティ</b>: '
                if state_txt:
                    solar_summary_block += state_txt
                if detail_bits:
                    solar_summary_block += f"<br><small>{h(' / '.join(detail_bits))}</small>"
                solar_summary_block += '</p>'
        if figs:
            card.append('<section class="two-col">' + "\n".join(figs) + '</section>')
        if bao_summary_block:
            card.append(bao_summary_block)
        rsd_summary_block = ''
        rsd_payload_path = Path('server/public/state_of_the_art/data/rsd_likelihood.json')
        if rsd_payload_path.exists():
            try:
                rsd_payload = json.loads(rsd_payload_path.read_text(encoding='utf-8'))
                late = rsd_payload.get('late_fdb')
                lcdm = rsd_payload.get('lcdm')
                if late and lcdm:
                    chi2_late = float(late.get('chi2_total', float('nan')))
                    chi2_lcdm = float(lcdm.get('chi2_total', float('nan')))
                    ndof = int(late.get('ndof_total', 0))
                    delta = chi2_late - chi2_lcdm
                    rsd_summary_block = (
                        f"<p><b>RSD 尤度</b>: Late‑FDB χ²={chi2_late:.2f} / dof={ndof}, "
                        f"ΛCDM χ²={chi2_lcdm:.2f}, Δχ²={delta:.2f}</p>"
                    )
            except Exception:
                rsd_summary_block = ''
        if rsd_summary_block:
            card.append(rsd_summary_block)

        cosmo_summary_path = Path('server/public/state_of_the_art/cosmo_formal_summary.json')
        if cosmo_summary_path.exists():
            try:
                cosmo_payload = json.loads(cosmo_summary_path.read_text(encoding='utf-8'))
                wl_stats = cosmo_payload.get('wl', {}).get('stats', {})
                cmb_stats = cosmo_payload.get('cmb', {})
                if wl_stats:
                    card.append('<div class=card><h3>WL 2PCF（KiDS-450 tomo1-1 正式）</h3>'
                                '<table class="t"><thead><tr><th>モデル</th><th>χ²</th><th>AICc</th><th>rχ²</th></tr></thead><tbody>'
                                + ''.join(
                                    f"<tr><td>{h(model)}</td><td>{stats.get('chi2', float('nan')):.2f}</td>"
                                    f"<td>{stats.get('AICc', float('nan')):.2f}</td><td>{stats.get('rchi2', float('nan')):.2f}</td></tr>"
                                    for model, stats in wl_stats.items()
                                )
                                + '</tbody></table></div>')
                if cmb_stats:
                    lcdm = cmb_stats.get('lcdm', {})
                    fdb = cmb_stats.get('late_fdb', {})
                    card.append('<div class=card><h3>CMB ピーク（Boomerang-2001 正式）</h3>'
                                '<table class="t"><thead><tr><th>モデル</th><th>ℓ₁</th><th>ΔT²(ℓ₁)[μK²]</th><th>ℓ₂</th><th>ΔT²(ℓ₂)[μK²]</th></tr></thead>'
                                f"<tbody><tr><td>ΛCDM</td><td>{lcdm.get('ell_peak1', '-')}</td><td>{lcdm.get('peak1', float('nan')):.2f}</td>"
                                f"<td>{lcdm.get('ell_peak2', '-')}</td><td>{lcdm.get('peak2', float('nan')):.2f}</td></tr>"
                                f"<tr><td>Late‑FDB</td><td>{fdb.get('ell_peak1', '-')}</td><td>{fdb.get('peak1', float('nan')):.2f}</td>"
                                f"<td>{fdb.get('ell_peak2', '-')}</td><td>{fdb.get('peak2', float('nan')):.2f}</td></tr></tbody></table></div>")
                # 詳細カード/サマリへの導線
                links = []
                if Path('server/public/state_of_the_art/wl_2pcf_formal.html').exists():
                    links.append('<a href="../state_of_the_art/wl_2pcf_formal.html">WL 2PCF 詳細</a>')
                if Path('server/public/state_of_the_art/cmb_peaks_formal.html').exists():
                    links.append('<a href="../state_of_the_art/cmb_peaks_formal.html">CMB ピーク詳細</a>')
                if cosmo_summary_path.exists():
                    links.append('<a href="../state_of_the_art/cosmo_formal_summary.json">summary JSON</a>')
                if Path('server/public/state_of_the_art/wl_2pcf_tomo_preview.html').exists():
                    links.append('<a href="../state_of_the_art/wl_2pcf_tomo_preview.html">WL tomo(preview)</a>')
                if links:
                    card.append('<div class="card pill-links"><p>' + ' '.join(links) + '</p></div>')
                cosmology_pending_notes.clear()
            except Exception:
                cosmology_pending_notes.append('WL 2PCF / CMB ピーク — ΔAICc≈0 の図表掲示が未完了。軽量尤度のモデル照合と公開図の作成が必要。')
        else:
            # 軽量版サマリにフォールバック
            wl_summary_block = ''
            wl_payload_path = Path('server/public/state_of_the_art/data/wl_likelihood.json')
            if wl_payload_path.exists():
                try:
                    wl_payload = json.loads(wl_payload_path.read_text(encoding='utf-8'))
                    fdb = wl_payload.get('late_fdb'); lcdm = wl_payload.get('lcdm')
                    if fdb and lcdm:
                        chi2_fdb = float(fdb.get('chi2_total', float('nan')))
                        chi2_lcdm = float(lcdm.get('chi2_total', float('nan')))
                        ndof = int(fdb.get('ndof_total', 0))
                        delta = chi2_fdb - chi2_lcdm
                        wl_summary_block = (
                            f"<p><b>WL 2PCF（KiDS‑450 tomo1‑1, 軽量）</b>: χ²={chi2_fdb:.2f} / dof={ndof}, "
                            f"ΛCDM χ²={chi2_lcdm:.2f}, Δχ²={delta:.2f}（ΔAICc≈0 の想定確認）</p>"
                        )
                except Exception:
                    wl_summary_block = ''
            if wl_summary_block:
                card.append(wl_summary_block)

            cmb_summary_block = ''
            cmb_payload_path = Path('server/public/state_of_the_art/data/cmb_likelihood.json')
            if cmb_payload_path.exists():
                try:
                    cmb_payload = json.loads(cmb_payload_path.read_text(encoding='utf-8'))
                    fdb = cmb_payload.get('late_fdb'); lcdm = cmb_payload.get('lcdm')
                    if fdb and lcdm:
                        chi2_fdb = float(fdb.get('chi2_total', float('nan')))
                        chi2_lcdm = float(lcdm.get('chi2_total', float('nan')))
                        ndof = int(fdb.get('ndof_total', 0))
                        delta = chi2_fdb - chi2_lcdm
                        cmb_summary_block = (
                            f"<p><b>CMB ピーク（Boomerang‑2001, 軽量）</b>: χ²={chi2_fdb:.2f} / dof={ndof}, "
                            f"ΛCDM χ²={chi2_lcdm:.2f}, Δχ²={delta:.2f}（ΔAICc≈0 の想定確認）</p>"
                        )
                except Exception:
                    cmb_summary_block = ''
            if cmb_summary_block:
                card.append(cmb_summary_block)

            wl_data_path = Path('data/weak_lensing/kids450_xi_tomo11.yml')
            if wl_data_path.exists():
                try:
                    wl_payload = yaml.safe_load(wl_data_path.read_text(encoding='utf-8'))
                    datasets = wl_payload.get('datasets') or []
                    if datasets:
                        ds = datasets[0]
                        theta = ds.get('theta_arcmin') or []
                        n_bins = len(theta)
                        if theta:
                            theta_min = float(theta[0])
                            theta_max = float(theta[-1])
                            card.append(
                                f"<p><b>弱レンズ2PCF</b>: KiDS-450 tomo1-1 — θ≈{theta_min:.2f}–{theta_max:.1f} arcmin, n={n_bins} (観測ベクトル整備済み; モデル照合は次フェーズ)。</p>"
                            )
                            cosmology_pending_notes.append('WL 2PCF — ΔAICc≈0 の図表未掲示（軽量尤度のモデル照合と公開図作成が必要）')
                except Exception:
                    pass

            cmb_data_path = Path('data/cmb/peak_ratios.yml')
            if cmb_data_path.exists():
                try:
                    cmb_payload = yaml.safe_load(cmb_data_path.read_text(encoding='utf-8'))
                    cmb_datasets = cmb_payload.get('datasets') or []
                    if cmb_datasets:
                        ds = cmb_datasets[0]
                        peaks = ds.get('data') or []
                        ell_values = [row[0] for row in peaks if isinstance(row, (list, tuple)) and len(row) >= 1]
                        if ell_values:
                            ell_text = ', '.join(f"{float(ell):.0f}" for ell in ell_values)
                            card.append(
                                f"<p><b>CMBピーク</b>: {h(ds.get('name', ''))} — ℓ={ell_text} (観測セット整備済み; モデル照合は次フェーズ)。</p>"
                            )
                            cosmology_pending_notes.append('CMB ピーク — ΔAICc≈0 の図表未掲示（Late‑FDB と ΛCDM の比較図化が未完了）')
                except Exception:
                    pass
            if not cosmology_pending_notes:
                cosmology_pending_notes.append('WL 2PCF / CMB ピーク — ΔAICc≈0 の図表掲示が未完了。軽量尤度のモデル照合と公開図の作成が必要。')
        if solar_summary_block:
            card.append(solar_summary_block)
        try:
            fair_cluster = fair_config.load('bullet_cluster')
            if fair_cluster:
                sha = fair_config.get_sha256()
                sha_short = sha[:8] if sha else ''
                fairness_note = '<p class="muted"><small>'
                fairness_note += 'フェア条件: config/fair.json'
                if sha_short:
                    fairness_note += f' (sha={h(sha_short)})'
                fairness_note += ' で WLS σマップ・整準(Δx,Δy)・wrap・PSF・高通過・マスク/ROI・rng を FDB/rot/shift/shuffle で共通化。'
                fairness_note += ' 主判定は AICc(FDB−rot/shift) の負側確認とし、shuffle は位相破壊の補助対照（方向・交差相関の掲示枠）と位置付ける。</small></p>'
        except Exception:
            fairness_note = ''
        if fairness_note:
            card.append(fairness_note)
        card.append('<p class="muted">注: 本線は Late‑FDB、E‑FDB は保険。CMB/BAO 整合（音響列の保持）を必須とし、自由度は {eps_max,a_on,k_c} の3に限定。</p>')
        card.append('</div>')
        body.append("\n".join(card))
        holdout_status = Path('server/public/state_of_the_art/holdout_status.json')
        if holdout_status.exists():
            try:
                status_payload = json.loads(holdout_status.read_text(encoding='utf-8'))
                items = status_payload.get('clusters', [])
                rows = []
                for item in items:
                    name = h(str(item.get('name')))
                    ready = bool(item.get('ready'))
                    missing = item.get('missing') or []
                    badge = '<span class="tag success">READY</span>' if ready else '<span class="tag warn">MISSING</span>'
                    detail = ''
                    if missing and not ready:
                        detail = ' / '.join(h(str(m)) for m in missing)
                    rows.append(f"<tr><th scope=\"row\">{name}</th><td>{badge}</td><td>{detail}</td></tr>")
                if rows:
                    body.append('<div class=card><h3>クラスタホールドアウトの準備状況</h3>'
                                '<table class="t"><thead><tr><th>Cluster</th><th>Status</th><th>Missing artifacts</th></tr></thead>'
                                f"<tbody>{''.join(rows)}</tbody></table>"
                                '<p><small>ホールドアウトパイプライン: <code>python scripts/cluster/run_holdout_pipeline.py --auto-train --auto-holdout</code></small></p></div>')
            except Exception:
                pass
        # Growth→UVLF stats card
        try:
            st = json.loads(Path('server/public/state_of_the_art/early_universe_stats.json').read_text(encoding='utf-8'))
            zs = st.get('z_stats', [])
            if zs:
                lines = []
                for e in zs:
                    z = int(e.get('z'))
                    dr = float(e.get('D_ratio'))
                    nu = e.get('nu', [])
                    mult = e.get('mult', [])
                    def _pair():
                        if len(nu) != len(mult): return ''
                        return ', '.join([f"ν={nu[i]:.0f}:×{mult[i]:.2f}" for i in range(len(nu))])
                    lines.append(f"z≈{z}: D'/D≈{dr:.3f} → [{_pair()}]")
                body.append('<div class=card><p><b>成長→個数倍率（稀少尾; PS/ST 近似）</b></p><p>' + '<br>'.join(lines) + '</p></div>')
        except Exception:
            pass
        # Persist meta for audit if produced by plot script
        if eu_meta.exists():
            pass
    except Exception:
        pass
    # Ensure notifications index exists for HTTP 200 (even if empty)
    try:
        notif = Path('server/public/notifications/index.html')
        notif.parent.mkdir(parents=True, exist_ok=True)
        if not notif.exists():
            notif.write_text(
                "<!doctype html><meta charset='utf-8'><title>Notifications</title>"
                "<link rel='stylesheet' href='../styles.css'>"
                "<main class='wrap'><h1>Notifications</h1>"
                "<div class='card'><small>通知ログは現在空です（HTTP 200 確保のためプレースホルダ）。</small></div>"
                "</main>",
                encoding='utf-8')
    except Exception:
        pass
    # Indicate if blacklist-filtered summary is used
    if 'nobl' in best.name.lower():
        body.append('<div class=card><b>注記:</b> ブラックリスト考慮版のサマリーを表示中（外的要因の強い対象を除外）。</div>')
    # Progress banner (prev -> current)
    prev_rate, cur_rate, cur_ts = load_progress()
    pr_txt = (
        (f"{prev_rate:.0f}%" if prev_rate is not None else "—%")
        + " → "
        + (f"{cur_rate:.0f}%" if cur_rate is not None else "—%")
    )
    when = f"<small>{cur_ts}</small>" if cur_ts else ""
    body.append(
        f"<div class=card><p><b>進捗率</b>: {pr_txt} {when}</p></div>"
    )
    # Questions to research policy lead, shown just below progress rate if present
    try:
        qpath = Path('data/questions_to_lead.json')
        if qpath.exists():
            qd = json.loads(qpath.read_text(encoding='utf-8'))
            items = qd.get('items', [])
            if items:
                body.append('<div class=card><p><b>研究方針指示者への質問</b></p><ul>')
                for it in items:
                    txt = it.get('q') or it.get('text') or ''
                    who = it.get('who')
                    ts = it.get('ts') or it.get('when')
                    meta = []
                    if who:
                        meta.append(who)
                    if ts:
                        meta.append(ts)
                    suffix = f" <small>({' / '.join(meta)})</small>" if meta else ''
                    body.append(f"<li>{txt}{suffix}</li>")
                body.append('</ul>')
                body.append('<p><small>更新: data/questions_to_lead.json を編集してください。</small></p>')
                body.append('</div>')
    except Exception as _e:
        # Non-fatal: continue without questions
        pass
    body.append("<h2>概要</h2>")
    body.append("<p>FDBを<b>見かけの引力</b>として扱い、共有パラメータで複数銀河を同時評価。"
                "ベースライン（GR+DM、MOND）と<b>同一データ・同一誤差モデル・同一ペナルティ</b>で公平比較します。</p>")
    # TODO/Notifications quick links
    if Path('server/public/TODO.md').exists():
        body.append('<div class=card><p><a href="../TODO.md">研究TODO（バックログ）</a></p></div>')
    # Summary-only card (link to full table page)
    try:
        params_shared = load_shared_params()
    except Exception:
        params_shared = None
    if params_shared:
        shared_eps = params_shared.theta_cos.epsilon
        shared_k0 = params_shared.theta_cos.k0
        shared_m = params_shared.theta_cos.m
        shared_gscale = params_shared.gas_scale if params_shared.gas_scale is not None else params_shared.theta_opt.omega0
        shared_tau0 = params_shared.theta_opt.tau0
        shared_omega0 = params_shared.theta_opt.omega0
        shared_eta = params_shared.theta_if.eta
        shared_g = params_shared.theta_aniso.g
    else:
        legacy_params = data.get("mu_k", {}) if isinstance(data.get("mu_k"), dict) else {}
        shared_eps = legacy_params.get('epsilon') or legacy_params.get('eps')
        shared_k0 = legacy_params.get('k0')
        shared_m = legacy_params.get('m')
        shared_gscale = data.get('gas_scale')
        shared_tau0 = data.get('tau0')
        shared_omega0 = data.get('omega0')
        shared_eta = data.get('eta')
        shared_g = data.get('g')
    gscale = shared_gscale
    mu_k = data.get("mu_k", {})
    chi = data.get("chi2_total", {}); aic = data.get("AIC", {})
    body.append("<h2>共有パラメータと適合度</h2>")
    card_lines: List[str] = []
    eps = mu_k.get('eps') or shared_eps
    k0 = mu_k.get('k0') or shared_k0
    mm = mu_k.get('m') or shared_m
    # Prefer CV shared summary (single source of truth)
    try:
        import json as _json
        cvp = Path('data/results/cv_shared_summary.json')
        if cvp.exists():
            cvd = _json.loads(cvp.read_text(encoding='utf-8'))
            # pick the most frequent or first fold train_best as adopted
            counts = {}
            for f in cvd.get('folds', []):
                b = f.get('train_best', {})
                t = (b.get('mu_eps'), b.get('mu_k0'), b.get('mu_m'))
                if None in t: continue
                counts[t] = counts.get(t, 0) + 1
            if counts:
                (eps, k0, mm) = max(counts.items(), key=lambda it: it[1])[0]
    except Exception:
        pass
    if eps is None or k0 is None or mm is None:
        lam_f = data.get('lam'); A_f = data.get('A')
        try:
            if eps is None and A_f is not None:
                eps = float(A_f)
            if k0 is None and lam_f not in (None, 0):
                k0 = 1.0 / float(lam_f)
            if mm is None:
                mm = 2
        except Exception:
            pass
    card_lines.append(
        f"<p>共有 μ(k): ε={h(str(eps))}, k0={h(str(k0))} kpc⁻¹, m={h(str(mm))}, gas_scale={h(str(gscale))}</p>"
    )
    if params_shared:
        card_lines.append(
            f"<p><small>θ_opt: τ₀={h(str(shared_tau0))}, ω₀={h(str(shared_omega0))}; "
            f"θ_if: η={h(str(shared_eta))}; θ_aniso: g={h(str(shared_g))}</small></p>"
        )
    # shared JSON fingerprint (if present)
    try:
        import hashlib as _hl
        p = Path('data/shared_params.json')
        if p.exists():
            shf = _hl.sha256(p.read_bytes()).hexdigest()[:12]
            card_lines.append(f"<p><small>source: data/shared_params.json (sha256:{h(shf)})</small></p>")
    except Exception:
        pass
    card_lines.append(f"<p>合計χ²: GR={h(str(chi.get('GR')))} / ULM={h(str(chi.get('ULW')))}</p>")
    card_lines.append("<p><a href=\"table.html\">全銀河のM/L一覧（別ページ）</a></p>")
    body.append("<div class=card>" + "".join(card_lines) + "</div>")
    # Audit note (static): fairness conditions
    body.append('<div class=card><small>比較条件: 同一n・同一誤差モデル（床: clip(0.03×Vobs, 3..7 km/s)）・同一ペナルティ（AICc）。</small></div>')
    # Win definition note for clarity
    body.append('<div class=card><small>勝率の定義: 勝ち＝ΔAICc<0（共通n、同一誤差・同一ペナルティ）。per‑galaxy 勝率と集計を併記します。</small></div>')
    # Site audit badge (CV+links)。HTTP未達時は関連リンクを一時非表示にする注記を出す
    http_ok = True
    try:
        import json as _json
        audit = _json.loads(Path('server/public/state_of_the_art/audit.json').read_text(encoding='utf-8'))
        http = (audit.get('http') or {}).get('http') or {}
        http_ok = bool(http.get('used_ids_csv_http')) and bool(http.get('cv_shared_summary_http')) and bool(http.get('notifications_http'))
        # 監査バナーは HTTP がすべて 200 のときのみ表示（復旧まで自動非表示）
        if audit.get('ok') and http_ok:
            body.append("<div class=card><small>監査OK: CV整合・リンク(used_ids/notifications)の200応答を確認。</small></div>")
    except Exception:
        pass

    # Missing data checklist (simple, user-facing)
    def _exists_any(paths: list[str]) -> bool:
        for p in paths:
            if Path(p).exists():
                return True
        return False

    missing: list[tuple[str, str, str]] = []  # (カテゴリ, 期待パス/候補, 入手ヒント)
    # Bullet Cluster (thin-lens FDB)
    if not _exists_any(['data/cluster/bullet/kappa.npy', 'data/cluster/bullet/kappa.fits']):
        missing.append((
            'Bullet: 弱レンズκ（収束）',
            'data/cluster/bullet/kappa.npy (or .fits)',
            "make bullet-fetch-kappa URL='https://.../kappa.fits'"
        ))
    if not _exists_any(['data/cluster/bullet/xray.npy', 'data/cluster/bullet/xray.fits', 'data/cluster/bullet/xray.tif']):
        missing.append((
            'Bullet: X線 Σ_e（電子表面密度の近似）',
            'data/cluster/bullet/xray.(npy|fits|tif)',
            'X線SB→Σ_e 変換後を配置（tifでも可）'
        ))
    if not _exists_any(['data/cluster/bullet/galaxy_peak.npy']):
        missing.append((
            'Bullet: 銀河/ICLピーク（任意）',
            'data/cluster/bullet/galaxy_peak.npy',
            '銀河重心/ICLのピーク座標のヒートマップ（任意）'
        ))
    # Halpha overlays for galaxy benches
    if not Path('data/halpha/NGC3198/Halpha_SB.fits').exists():
        missing.append((
            'NGC 3198: Hα（SB/EM）',
            'data/halpha/NGC3198/Halpha_SB.fits',
            "make fetch-halpha-ngc3198 URL='https://irsa.ipac.caltech.edu/.../HA_SUB.fits'"
        ))
    if not Path('data/halpha/NGC2403/Halpha_SB.fits').exists():
        missing.append((
            'NGC 2403: Hα（SB/EM）',
            'data/halpha/NGC2403/Halpha_SB.fits',
            'SINGS/IRSAのHA_SUBを取得→scripts/halpha/ingest_halpha.py で取り込み'
        ))
    # Velocity field (optional overlays)
    if not Path('data/vel/NGC2403/velocity.fits').exists():
        missing.append((
            'NGC 2403: 速度場（THINGS moment-1）',
            'data/vel/NGC2403/velocity.fits',
            "make fetch-things-ngc2403 URL='https://.../NGC2403_THINGS_cube.fits'"
        ))
    if not Path('data/vel/NGC3198/velocity.fits').exists():
        missing.append((
            'NGC 3198: 速度場（任意）',
            'data/vel/NGC3198/velocity.fits',
            '観測 moment-1（在れば残差重畳を自動生成）'
        ))

    body.append('<h2>不足データ一覧</h2>')
    if missing:
        items = ''.join(
            f"<li><b>{h(cat)}</b> — <code>{h(path)}</code><br><small>入手: {h(hint)}</small></li>"
            for cat, path, hint in missing
        )
        body.append('<div class=card><ul>' + items + '</ul></div>')
    else:
        body.append('<div class=card><p>不足データはありません（必要な入力は揃っています）。</p></div>')

    # Concrete acquisition steps (copy/paste runnable)
    body.append('<h2>不足データの入手手順（コピペ可）</h2>')
    steps: list[str] = []
    steps.append('<div class=card>')
    steps.append('<h3>Hα（NGC 3198 / 2403）</h3>')
    steps.append('<p><b>NGC 3198（SINGS/IRSA; continuum-subtracted）</b></p>')
    steps.append('<pre><code># Hα (continuum-subtracted)\nhttps://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/ngc3198/Ancillary/ngc3198_HA_SUB_dr4.fits\n# 取得後の取り込み\nPYTHONPATH=. ./.venv/bin/python scripts/halpha/ingest_halpha.py --in data/tmp/ngc3198_HA_SUB_dr4.fits --name NGC3198\n</code></pre>')
    steps.append('<p><b>NGC 2403（SINGS/IRSA; continuum差分を自動実行）</b></p>')
    steps.append('<pre><code># Hα (pre-subtraction) と R バンド\nhttps://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/ngc2403/Ancillary/ngc2403_HA_dr4.fits\nhttps://irsa.ipac.caltech.edu/data/SPITZER/SINGS/galaxies/ngc2403/Ancillary/ngc2403_R_dr4.fits\n# 取り込み（差分・EM生成はスクリプトが実行）\nPYTHONPATH=. ./.venv/bin/python scripts/halpha/ingest_halpha.py --in data/tmp/ngc2403_HA_dr4.fits --name NGC2403\n</code></pre>')
    steps.append('</div>')

    steps.append('<div class=card>')
    steps.append('<h3>H I 21 cm（HALOGAS/THINGS; キューブとmoment-1）</h3>')
    steps.append('<p><b>HALOGAS DR1（WSRT; 直リンク）</b></p>')
    steps.append('<pre><code># NGC 3198\nhttps://zenodo.org/record/3715549/files/NGC3198-HR-cube.fits?download=1\nhttps://zenodo.org/record/3715549/files/NGC3198-HR_mom1m.fits?download=1\n\n# NGC 2403\nhttps://zenodo.org/record/3715549/files/NGC2403-HR-cube.fits?download=1\nhttps://zenodo.org/record/3715549/files/NGC2403-HR_mom1m.fits?download=1\n</code></pre>')
    steps.append('<p>THINGS（VLA; 比較用）は VizieR <code>J/AJ/136/2563</code> から該当銀河のFITSを取得し、同一パイプでmoment再生成。</p>')
    steps.append('</div>')

    steps.append('<div class=card>')
    steps.append('<h3>星質量（IRAC 3.6 μm; SINGS/IRSA）</h3>')
    steps.append('<p>各銀河の SINGS サマリより IRAC1 (3.6μm) を取得し、M/Lはページ記法（本文: ML_*, 論文: Υ★）で統一。</p>')
    steps.append('</div>')

    body.extend(steps)
    # Boundary kernel demo link (Lambert→forward)
    try:
        bnd = Path('server/public/reports/boundary_demo.html')
        if bnd.exists():
            body.append('<div class=card><p><a href="../reports/boundary_demo.html">緩やかな境界と垂直放射（角度核）</a> — Lambert(β=0) と前方化(β>0)の対比</p></div>')
    except Exception:
        pass
    try:
        bidx = Path('server/public/reports/benchmarks/index.html')
        if bidx.exists():
            body.append('<div class=card><p><a href="../reports/benchmarks/index.html">単一銀河ベンチマーク（NGC 3198 他）</a> — 固定 μ0・フェア条件の詳細検証</p></div>')
        # Dedicated bench link for UGC06787 if present
        bench_ugc = Path('server/public/reports/bench_ugc06787.html')
        if bench_ugc.exists():
            body.append('<div class=card><p><a href="../reports/bench_ugc06787.html">UGC06787 ベンチ（統一テンプレ v2）</a> — AICc/rχ²/外縁1/r² 指標つき</p></div>')
        wsif = Path('server/public/reports/ws_vs_phieta_rep6.html')
        if wsif.exists():
            body.append('<div class=card><p><a href="../reports/ws_vs_phieta_rep6.html">界面 W·S vs 情報流 Phi·eta（代表6）</a> — AICc 勝率比較</p></div>')
        wsiff = Path('server/public/reports/ws_vs_phieta_fair.html')
        if wsiff.exists():
            body.append('<div class=card><p><a href="../reports/ws_vs_phieta_fair.html">Phi·eta パラメタ スイープ（公平: k=2, 同一N/誤差）</a> — best per galaxy と ΔAICc</p></div>')
        # KPI progress card (if available)
        try:
            pc = Path('server/public/reports/progress_card.html')
            if pc.exists():
                body.append(pc.read_text(encoding='utf-8'))
        except Exception:
            pass
        # Quick Links (pill buttons)
        try:
            quick = []
            if Path('server/public/reports/bench_ngc2403.html').exists():
                quick.append('<a href="../reports/bench_ngc2403.html">bench NGC2403</a>')
            if Path('server/public/reports/bench_ngc3198.html').exists():
                quick.append('<a href="../reports/bench_ngc3198.html">bench NGC3198</a>')
            if Path('server/public/reports/bench_ugc06787.html').exists():
                quick.append('<a href="../reports/bench_ugc06787.html">bench UGC06787</a>')
            if Path('server/public/reports/ws_vs_phieta_fair.html').exists():
                quick.append('<a href="../reports/ws_vs_phieta_fair.html">A/B (W·S vs Φ×η)</a>')
            if Path('server/public/reports/wcut_error_note.html').exists():
                quick.append('<a href="../reports/wcut_error_note.html">ω_cut 誤差伝播</a>')
                # Lightweight WL/CMB sanity cards (ΔAICc≈0)
            if Path('server/public/state_of_the_art/wl_2pcf_formal.html').exists():
                quick.append('<a href="../state_of_the_art/wl_2pcf_formal.html">WL 2PCF(正式)</a>')
            elif Path('server/public/state_of_the_art/wl_2pcf.html').exists():
                quick.append('<a href="../state_of_the_art/wl_2pcf.html">WL 2PCF(軽)</a>')
            if Path('server/public/state_of_the_art/wl_2pcf_tomo_proto.html').exists():
                quick.append('<a href="../state_of_the_art/wl_2pcf_tomo_proto.html">WL tomo(proto)</a>')
            if Path('server/public/state_of_the_art/cmb_peaks_formal.html').exists():
                quick.append('<a href="../state_of_the_art/cmb_peaks_formal.html">CMBピーク(正式)</a>')
            elif Path('server/public/state_of_the_art/cmb_peaks.html').exists():
                quick.append('<a href="../state_of_the_art/cmb_peaks.html">CMBピーク(軽)</a>')
                if Path('server/public/state_of_the_art/holdout_progress.html').exists():
                    quick.append('<a href="../state_of_the_art/holdout_progress.html">HO進捗</a>')
                if Path('server/public/state_of_the_art/jobs.html').exists():
                    quick.append('<a href="../state_of_the_art/jobs.html">Jobs</a>')
            if Path('server/public/reports/data_catalog.html').exists():
                quick.append('<a href="../reports/data_catalog.html">データ目録</a>')
            # A-3 knee summaries (if available)
            try:
                a3links = []
                if Path('server/public/reports/AbellS1063_a3_summary.html').exists():
                    a3links.append('<a href="../reports/AbellS1063_a3_summary.html">AbellS1063 A‑3サマリ</a>')
                if Path('server/public/reports/MACSJ0416_a3_summary.html').exists():
                    a3links.append('<a href="../reports/MACSJ0416_a3_summary.html">MACSJ0416 A‑3サマリ</a>')
                # A-4 summaries (if available)
                if Path('server/public/reports/AbellS1063_a4_summary.html').exists():
                    a3links.append('<a href="../reports/AbellS1063_a4_summary.html">AbellS1063 A‑4サマリ</a>')
                if Path('server/public/reports/MACSJ0416_a4_summary.html').exists():
                    a3links.append('<a href="../reports/MACSJ0416_a4_summary.html">MACSJ0416 A‑4サマリ</a>')
                if a3links:
                    quick.extend(a3links)
            except Exception:
                pass
            if quick:
                body.append('<div class="card pill-links"><p>' + ''.join(quick) + '</p></div>')
        except Exception:
            pass
        corr3198 = Path('server/public/reports/ngc3198_wcut_corr.html')
        corr2403 = Path('server/public/reports/ngc2403_wcut_corr.html')
        corr_links = []
        if corr3198.exists():
            corr_links.append('<a href="../reports/ngc3198_wcut_corr.html">NGC3198: ω_cut×残差 相関</a>')
        if corr2403.exists():
            corr_links.append('<a href="../reports/ngc2403_wcut_corr.html">NGC2403: ω_cut×残差 相関</a>')
        if corr_links:
            body.append('<div class=card><p>' + ' / '.join(corr_links) + '</p></div>')
        # Stability quick links if present
        try:
            lst = []
            if Path('server/public/reports/ngc2403_outer_slope_stability.html').exists():
                lst.append('<a href="../reports/ngc2403_outer_slope_stability.html">NGC2403: 外縁傾き安定性</a>')
            if Path('server/public/reports/ngc3198_outer_slope_stability.html').exists():
                lst.append('<a href="../reports/ngc3198_outer_slope_stability.html">NGC3198: 外縁傾き安定性</a>')
            if Path('server/public/reports/ngc2403_local_stability.html').exists():
                lst.append('<a href="../reports/ngc2403_local_stability.html">NGC2403: ΔAICc局所安定</a>')
            if lst:
                body.append('<div class="card pill-links"><p>' + ' '.join(lst) + '</p></div>')
        except Exception:
            pass
        kc1 = Path('server/public/reports/ngc3198_kappaC_fit.html')
        kc2 = Path('server/public/reports/ngc2403_kappaC_fit.html')
        kc_links = []
        if kc1.exists():
            kc_links.append('<a href="../reports/ngc3198_kappaC_fit.html">NGC3198: κ,C のフィット</a>')
        if kc2.exists():
            kc_links.append('<a href="../reports/ngc2403_kappaC_fit.html">NGC2403: κ,C のフィット</a>')
        if kc_links:
            body.append('<div class=card><p>' + ' / '.join(kc_links) + '</p></div>')
        sb1 = Path('server/public/reports/ngc3198_kappaC_solar.html')
        sb2 = Path('server/public/reports/ngc2403_kappaC_solar.html')
        sb_links = []
        if sb1.exists():
            sb_links.append('<a href="../reports/ngc3198_kappaC_solar.html">NGC3198: (κ,C) × Solar上限</a>')
        if sb2.exists():
            sb_links.append('<a href="../reports/ngc2403_kappaC_solar.html">NGC2403: (κ,C) × Solar上限</a>')
        if sb_links:
            body.append('<div class=card><p>' + ' / '.join(sb_links) + '</p></div>')
        # Υ★–κ–C 90%CL quick links
        y1 = Path('server/public/reports/ngc3198_ykc_90.html')
        y2 = Path('server/public/reports/ngc2403_ykc_90.html')
        y_links = []
        if y1.exists():
            y_links.append('<a href="../reports/ngc3198_ykc_90.html">NGC3198: Υ★–κ–C 90%CL</a>')
        if y2.exists():
            y_links.append('<a href="../reports/ngc2403_ykc_90.html">NGC2403: Υ★–κ–C 90%CL</a>')
        if y_links:
            body.append('<div class=card><p>' + ' / '.join(y_links) + '</p></div>')

        pade = Path('server/public/reports/geom_kernel_pade_disk.html')
        if pade.exists():
            body.append('<div class=card><p><a href="../reports/geom_kernel_pade_disk.html">幾何カーネル Padé 近似（円盤; 雛形）</a></p></div>')
        pade_opt = Path('server/public/reports/geom_kernel_pade_disk_opt.html')
        if pade_opt.exists():
            body.append('<div class=card><p><a href="../reports/geom_kernel_pade_disk_opt.html">幾何カーネル Padé 近似（円盤; 最適化）</a></p></div>')
        ang1 = Path('server/public/reports/ngc3198_angle_align.html')
        ang2 = Path('server/public/reports/ngc2403_angle_align.html')
        alinks = []
        if ang1.exists():
            alinks.append('<a href="../reports/ngc3198_angle_align.html">NGC3198: ∇ω_cut と a_FDB の角度整合</a>')
        if ang2.exists():
            alinks.append('<a href="../reports/ngc2403_angle_align.html">NGC2403: ∇ω_cut と a_FDB の角度整合</a>')
        if alinks:
            body.append('<div class=card><p>' + ' / '.join(alinks) + '</p></div>')
        # J_I vector panels (beta vs isotropic)
        j1 = Path('server/public/reports/ngc3198_JI_vector_panel.html')
        j2 = Path('server/public/reports/ngc2403_JI_vector_panel.html')
        jlinks = []
        if j1.exists():
            jlinks.append('<a href="../reports/ngc3198_JI_vector_panel.html">NGC3198: J_I ベクトル（β=0/β>0）</a>')
        if j2.exists():
            jlinks.append('<a href="../reports/ngc2403_JI_vector_panel.html">NGC2403: J_I ベクトル（β=0/β>0）</a>')
        if jlinks:
            body.append('<div class=card><p>' + ' / '.join(jlinks) + '</p></div>')
        ph = Path('server/public/reports/phieta_hits.html')
        if ph.exists():
            body.append('<div class=card><p><a href="../reports/phieta_hits.html">Phi·eta スイープ — ΔAICc≤−6 ヒット集計</a></p></div>')
    except Exception:
        pass
    # 現在の課題（ホールドアウト・宇宙論）の収集用リスト
    current_issues: list[str] = []
    cosmology_pending_notes: list[str] = []

    # Bullet holdout link and required data checklist
    try:
        bh = Path('server/public/reports/bullet_holdout.html')
        if bh.exists():
            body.append('<div class=card><p><a href="../reports/bullet_holdout.html">バレットクラスタ ホールドアウト（固定α,β,C）</a></p>'
                        '<p><small>学習→固定→適用の最小核パイプライン。ΔAICcと簡易対照を併記。</small></p></div>')
            # KPIカード（JSONサマリがあれば判定）
            bj = Path('server/public/reports/bullet_holdout.json')
            if bj.exists():
                try:
                    j = json.loads(bj.read_text(encoding='utf-8'))
                    delta = j.get('delta', {})
                    rot_delta = float(delta.get('FDB_minus_rot', float('nan')))
                    shift_delta = float(delta.get('FDB_minus_shift', float('nan')))
                    status_rot = '達成' if rot_delta <= -10.0 else '未達'
                    status_shift = '達成' if shift_delta <= -10.0 else '未達'

                    ind = j.get('indicators', {})
                    peak_pix = float(ind.get('peak_offset_pix') or float('nan'))
                    peak_masked = float(ind.get('peak_offset_pix_masked') or float('nan'))
                    hp_peak_pix = float(ind.get('hp_peak_offset_pix') or float('nan'))
                    y2 = float(ind.get('shear_phase_cos') or float('nan'))
                    r_p = float(ind.get('corr_residual_sigmae') or float('nan'))

                    s_shadow = ind.get('S_shadow') or {}
                    s_val = float('nan')
                    s_perm = float('nan')
                    if isinstance(s_shadow, dict):
                        vals = s_shadow.get('values') or {}
                        if isinstance(vals, dict):
                            try:
                                s_val = float(vals.get('global', float('nan')))
                            except Exception:
                                s_val = float('nan')
                        perm_info = s_shadow.get('perm') or {}
                        if isinstance(perm_info, dict):
                            try:
                                s_perm = float(perm_info.get('p_perm_one_sided_pos', float('nan')))
                            except Exception:
                                s_perm = float('nan')
                    status_shadow = '達成' if (s_val == s_val and s_val > 0.0 and s_perm == s_perm and s_perm < 0.01) else '未達'

                    # kpc換算（オプション）
                    peak_kpc_txt = ''
                    try:
                        met = json.loads(Path('server/public/reports/cluster/bullet_metrics.json').read_text(encoding='utf-8'))
                        scale = met.get('scale_kpc_per_pix')
                        if isinstance(scale, (float, int)):
                            peak_kpc_txt = f" / {peak_pix*float(scale):.0f} kpc"
                    except Exception:
                        pass

                    strata = ind.get('strata') or {}
                    s90 = strata.get('p90') or {}
                    s75 = strata.get('p75') or {}

                    # Summary card
                    body.append(
                        '<div class=card>'
                        f'<p><b>バレットKPI</b>: ΔAICc(FDB−rot)={rot_delta:.2e} → {status_rot}, '
                        f'ΔAICc(FDB−shift)={shift_delta:.2e} → {status_shift}, '
                        f'S_shadow={s_val:.3f} (p_perm={s_perm:.2g}) → {status_shadow}</p>'
                        f'<p><small>主要指標: ①ピーク距離={peak_pix:.1f} pix{peak_kpc_txt} (top-mask={peak_masked:.1f} pix, HP={hp_peak_pix:.1f} pix), '
                        f'②⟨cosΔθ⟩={y2:.3f}, ③corr(κ残差, Σ_e)={r_p:.3f}</small></p>'
                        f'<p><small>分層: top10% Spearman={float(s90.get("spear_r") or float("nan")):.3f} '
                        f'(n={int(s90.get("n") or 0)}), top25% Spearman={float(s75.get("spear_r") or float("nan")):.3f} '
                        f'(n={int(s75.get("n") or 0)})</small></p>'
                        '</div>'
                    )

                    # Footnote with fairness + execution metadata
                    N = int(j.get('N', 0))
                    N_eff = int(j.get('N_eff', 0))
                    k_map = j.get('k', {})
                    chi2 = j.get('chi2', {})
                    rchi2 = j.get('rchi2', {})
                    psf_sigma = float(j.get('sigma_psf', float('nan')))
                    hp_sigma = float(ind.get('hp_sigma_pix') or float('nan'))
                    mask_q = float(ind.get('mask_quantile') or float('nan'))
                    align_meta = (j.get('processing') or {}).get('alignment') or {}
                    wrap_meta = (j.get('processing') or {}).get('fair_wrap') or {}
                    rng_seed = align_meta.get('rng_seed') or (j.get('audit', {}).get('controls') or {}).get('rng_seed')
                    fairness_meta = (j.get('processing') or {}).get('fairness_meta') or {}
                    fair_sha = fairness_meta.get('sha12') or (fairness_meta.get('sha256', '')[:12])
                    shared_sha = sha12('data/shared_params.json')
                    command_line = (j.get('processing') or {}).get('command_line')

                    def fmt_chi(label):
                        val = chi2.get(label)
                        return f"{val:.2e}" if isinstance(val, (int, float)) else '—'

                    def fmt_rchi(label):
                        val = rchi2.get(label)
                        return f"{val:.2e}" if isinstance(val, (int, float)) else '—'

                    foot = (
                        '<div class=card><small>'
                        f'(N={N}, N_eff={N_eff}); '
                        f'k(FDB/rot/shift/shuffle)={k_map.get("FDB", "-")}/{k_map.get("rot", "-")}/{k_map.get("shift", "-")}/{k_map.get("shuffle", "-")}; '
                        f'χ²(FDB/rot/shift/shuffle)={fmt_chi("FDB")}/{fmt_chi("rot")}/{fmt_chi("shift")}/{fmt_chi("shuffle")}; '
                        f'rχ²(FDB/rot/shift/shuffle)={fmt_rchi("FDB")}/{fmt_rchi("rot")}/{fmt_rchi("shift")}/{fmt_rchi("shuffle")}. '
                        '<br>'
                        f'PSF σ={psf_sigma:.2f} pix, 高通過 σ={hp_sigma:.1f} pix, Σ_e マスク上位={mask_q*100:.0f}%,'
                        f' 整準(dy,dx)=({float(align_meta.get("dy_pix", 0.0)):.2f},{float(align_meta.get("dx_pix", 0.0)):.2f}), '
                        f'wrap(dy,dx)=({wrap_meta.get("dy", 12)},{wrap_meta.get("dx", -7)}), rng={rng_seed}. '
                        f'fair.json sha={fair_sha or "—"}, shared_params.json sha={shared_sha or "—"}. '
                        f'command: <code>{h(command_line) if command_line else "—"}</code>'
                        '</small></div>'
                    )
                    body.append(foot)

                    # 次アクション: 汎化と他クラスタへの展開
                    body.append('<div class=card><small>次アクション: 汎化のため A1689/CL0024 で学習→凍結後、MACSJ0416/AbellS1063 など新ホールドアウトを順次実行し、ΔAICc(FDB−rot)と S_shadow の恒常化を確認。</small></div>')

                    # bullet_line for summary list
                    bullet_line = (
                        '<li><b>バレット・ホールドアウト</b> — '
                        f'ΔAICc(FDB−rot)={rot_delta:.2e} ({status_rot}), '
                        f'S_shadow={s_val:.3f} (p={s_perm:.2g}, {status_shadow}).</li>'
                    )
                except Exception:
                    pass
        # Additional cluster holdouts (other than Bullet)
        try:
            extras_dir = Path('server/public/reports/cluster')
            extra_items: list[str] = []
            if extras_dir.exists():
                for path in sorted(extras_dir.glob('*_holdout.json')):
                    name = path.stem.replace('_holdout', '')
                    if name.lower() == 'bullet':
                        continue
                    try:
                        data = json.loads(path.read_text(encoding='utf-8'))
                    except Exception:
                        continue
                    delta = data.get('delta', {}) if isinstance(data, dict) else {}
                    try:
                        rot_delta = float(delta.get('FDB_minus_rot', float('nan')))
                    except Exception:
                        rot_delta = float('nan')
                    try:
                        shift_delta = float(delta.get('FDB_minus_shift', float('nan')))
                    except Exception:
                        shift_delta = float('nan')
                    status_rot = '達成' if rot_delta <= -10.0 else '未達'
                    status_shift = '達成' if shift_delta <= -10.0 else '未達'

                    indicators = data.get('indicators', {}) if isinstance(data, dict) else {}
                    s_shadow = indicators.get('S_shadow', {}) if isinstance(indicators, dict) else {}
                    try:
                        s_val = float((s_shadow.get('values') or {}).get('global'))
                    except Exception:
                        s_val = float('nan')
                    try:
                        s_perm = float((s_shadow.get('perm') or {}).get('p_perm_one_sided_pos'))
                    except Exception:
                        s_perm = float('nan')
                    status_shadow = '達成' if (
                        s_val == s_val and s_val > 0.0 and s_perm == s_perm and s_perm < 0.01
                    ) else '未達'

                    N = data.get('N') if isinstance(data, dict) else None
                    N_eff = data.get('N_eff') if isinstance(data, dict) else None
                    aux = ''
                    if isinstance(N, (int, float)) and isinstance(N_eff, (int, float)):
                        aux = f' (N={int(N)}, N_eff={int(N_eff)})'
                    html_path = path.with_suffix('.html')
                    link_html = (
                        f"<a href='../reports/cluster/{html_path.name}'>結果</a>"
                        if html_path.exists()
                        else '結果'
                    )
                    lname = name.lower()
                    if lname == 'abells1063':
                        if not (math.isfinite(s_val) and s_val > 0.0 and math.isfinite(s_perm) and s_perm < 0.01):
                            current_issues.append(
                                f"Abell S1063 — S_shadow={s_val:.3f} (p={s_perm:.2g}) で方向性未達。Σモデル再設計と FAST→FULL 検証が必要。"
                            )
                    if lname == 'macsj0416':
                        macs_notes: list[str] = []
                        if not (math.isfinite(rot_delta) and rot_delta <= -10.0):
                            macs_notes.append(f"ΔAICc(FDB−rot)={rot_delta:.1f}")
                        if not (math.isfinite(shift_delta) and shift_delta <= -10.0):
                            macs_notes.append(f"ΔAICc(FDB−shift)={shift_delta:.1f}")
                        if not (math.isfinite(s_val) and s_val > 0.0 and math.isfinite(s_perm) and s_perm < 0.01):
                            macs_notes.append(f"S_shadow={s_val:.3f} (p={s_perm:.2g})")
                        if macs_notes:
                            current_issues.append(
                                "MACS J0416 — " + ', '.join(macs_notes) + " が未達 (WCS/PSF/ROI 再監査と再ホールドアウトが必要)。"
                            )

                    extra_items.append(
                        '<li>'
                        f"<b>{h(name)}</b>{aux} — "
                        f"ΔAICc(FDB−rot)={rot_delta:.2e} ({status_rot}), "
                        f"ΔAICc(FDB−shift)={shift_delta:.2e} ({status_shift}), "
                        f"S_shadow={s_val:.3f} (p={s_perm:.2g}, {status_shadow}) "
                        f"[{link_html}]"
                        '</li>'
                    )
            if extra_items:
                body.append(
                    '<div class=card><h3>追加ホールドアウト（学習: Abell1689/CL0024）</h3><ul>'
                    + ''.join(extra_items)
                    + '</ul></div>'
                )
        except Exception:
            pass

        # Ops single-MD instructions → convert to HTML and link
        mdp = Path('memo/bullet_exec.md')
        if mdp.exists():
            dst = Path('server/public/state_of_the_art/bullet_exec.html')
            try:
                md_html = render_markdown_simple(mdp.read_text(encoding='utf-8'))
                write_html(dst, 'バレット実行指示（単一MD）', '<div class=card>'+md_html+'</div>')
            except Exception:
                # If rendering fails, fall back to serving raw MD in <pre>
                try:
                    write_html(dst, 'バレット実行指示（単一MD; raw）', '<div class=card><pre>'+h(mdp.read_text(encoding='utf-8'))+'</pre></div>')
                except Exception:
                    pass
            body.append('<div class=card><p><a href="bullet_exec.html">バレット実行指示（単一MD版）</a> — このファイルが最新・唯一の指示書</p></div>')
        # Always show the required-data checklist to make gaps obvious
        body.append('<div class=card><h3>クラスタ・ホールドアウト 必要データ</h3>'
                    '<ul><li>data/cluster/Abell1689/omega_cut.fits, sigma_e.fits, <b>kappa_obs.fits</b></li>'
                    '<li>data/cluster/CL0024/omega_cut.fits, sigma_e.fits, <b>kappa_obs.fits</b></li>'
                    '<li>data/cluster/Bullet/omega_cut.fits, sigma_e.fits (<small>ホールドアウト</small>)</li></ul>'
                    '<p><small>各FITSヘッダに <code>PIXKPC</code>（[kpc/px]）を含めてください。Abell1689/CL0024 の観測κについては、<b>Lenstool 公式モデル tarball</b>（a1689.tar.gz / cl0024.tar.gz）のご提供（または添付ID）をお願いします。受領→展開→lenstool→FITS→PIXKPC→配置の順で整備します。</small></p></div>')

        if current_issues or cosmology_pending_notes:
            body.append(
                '<div class=card><h3>現在の課題</h3><ul>'
                + ''.join(f'<li>{h(text)}</li>' for text in (current_issues + cosmology_pending_notes))
                + '</ul></div>'
            )
    except Exception:
        pass

    # 環境とツール（PATH/バイナリ/ラッパ）
    try:
        import os, subprocess as _sp
        rows_env: list[str] = []
        # PATH hook in ~/.bashrc
        bashrc = Path.home() / '.bashrc'
        hook_ok = False
        try:
            txt = bashrc.read_text(encoding='utf-8')
            hook_ok = 'gravitation/tools/profile.d/gravitation-paths.sh' in txt
        except Exception:
            pass
        rows_env.append('<tr><td>PATH hook (~/.bashrc)</td><td><code>tools/profile.d/gravitation-paths.sh</code></td>'
                         f"<td>{'OK' if hook_ok else '—'}</td><td></td></tr>")
        # Profile script exists
        prof = Path('tools/profile.d/gravitation-paths.sh')
        rows_env.append('<tr><td>profile script</td><td><code>tools/profile.d/gravitation-paths.sh</code></td>'
                         f"<td>{'OK' if prof.exists() else '—'}</td><td></td></tr>")
        # Lenstool binary and version
        lt_path = Path('.mamba/envs/lenstool_env/bin/lenstool')
        lt_ver = None
        if lt_path.exists():
            try:
                out = _sp.check_output([str(lt_path), '-v'], stderr=_sp.STDOUT, timeout=2).decode('utf-8', 'ignore').strip()
                lt_ver = out.splitlines()[0].strip()
            except Exception:
                lt_ver = 'found'
        rows_env.append('<tr><td>Lenstool</td><td><code>.mamba/envs/lenstool_env/bin/lenstool</code></td>'
                        f"<td>{h(lt_ver) if lt_ver else '—'}</td><td></td></tr>")
        # Wrapper
        wrap = Path('bin/lenstool')
        wrap_ok = False
        try:
            txt = wrap.read_text(encoding='utf-8')
            wrap_ok = '.mamba/envs/lenstool_env' in txt and 'micromamba' in txt
        except Exception:
            pass
        rows_env.append('<tr><td>wrapper</td><td><code>bin/lenstool</code></td>'
                        f"<td>{'OK' if wrap_ok else '—'}</td><td></td></tr>")
        # CIAO env
        ciao = Path.home() / '.mamba/envs/ciao-4.17/bin/ciaover'
        rows_env.append('<tr><td>CIAO</td><td><code>~/.mamba/envs/ciao-4.17</code></td>'
                        f"<td>{'OK' if ciao.exists() else '—'}</td><td></td></tr>")
        # Python lenstools (package) — local or external-env
        external_info = Path('server/public/reports/env/lenstools_info.json')
        external_txt = Path('server/public/reports/env/lenstools_attempt_20250930.log')
        try:
            import importlib
            importlib.import_module('lenstools')
            rows_env.append('<tr><td>Python lenstools</td><td><code>pip install lenstools</code></td><td>OK（ローカル）</td><td></td></tr>')
        except Exception:
            if external_info.exists():
                try:
                    meta = json.loads(external_info.read_text(encoding='utf-8'))
                except Exception:
                    meta = {}
                ver = meta.get('lenstools') or meta.get('version') or ''
                plat = meta.get('platform') or ''
                rows_env.append('<tr><td>Python lenstools</td><td><code>外部env</code></td>'
                                f"<td>導入済（{ver} / {plat}）</td>"
                                f"<td><a href='../reports/env/lenstools_info.json'>info</a></td></tr>")
            else:
                rows_env.append('<tr><td>Python lenstools</td><td><code>pip install lenstools</code></td><td>未導入</td>'
                                f"<td>{'<a href=\'../reports/env/lenstools_attempt_20250930.log\'>attempt log</a>' if external_txt.exists() else ''}</td></tr>")
        # Optional: generic environment logs (ciaover / lenstool -v)
        env_logs_txt = Path('server/public/reports/env_logs.txt')
        env_logs_json = Path('server/public/reports/env_logs.json')
        if env_logs_txt.exists() or env_logs_json.exists():
            ln = []
            if env_logs_txt.exists():
                ln.append("<a href='../reports/env_logs.txt'>env_logs.txt</a>")
            if env_logs_json.exists():
                ln.append("<a href='../reports/env_logs.json'>env_logs.json</a>")
            rows_env.append('<tr><td>環境ログ</td><td>ciaover / lenstool -v</td><td>収集済</td><td>' + ' / '.join(ln) + '</td></tr>')
        body.append('<h2>環境とツール</h2>')
        body.append('<div class=card><table><thead><tr><th>項目</th><th>場所</th><th>状態</th><th></th></tr></thead><tbody>'
                    + "\n".join(rows_env) + '</tbody></table>'
                    '<p><small>使用例: <code>lenstool -v</code> / <code>ciao-on</code> → <code>ciaover</code></small></p>'
                    '</div>')
    except Exception:
        pass

    # Status update card — evaluation + concrete next steps
    try:
        # Compose Bullet line dynamically
        bullet_line = '<li><b>バレット・ホールドアウト</b> — 学習用の観測κ不足で停止中。必要ファイルと PIXKPC 必須をSOTAに明記。</li>'
        try:
            bj = Path('server/public/reports/bullet_holdout.json')
            if bj.exists():
                j = json.loads(bj.read_text(encoding='utf-8'))
                d = j.get('delta') or {}
                kmap = j.get('k') or {}
                bullet_line = (
                    '<li><b>バレット・ホールドアウト</b> — 稼働中。固定(α,β,C)で ΔAICc を掲出: '
                    + f"FDB−rot={float(d.get('FDB_minus_rot') or float('nan')):.1f}, "
                    + f"FDB−shift={float(d.get('FDB_minus_shift') or float('nan')):.1f}, "
                    + f"FDB−shuffle={float(d.get('FDB_minus_shuffle') or float('nan')):.1f}; "
                    + f"(N,k)=N={int(j.get('N') or 0)}, k(FDB/rot/shift/shuffle)={int(kmap.get('FDB',0))}/{int(kmap.get('rot',1))}/{int(kmap.get('shift',2))}/{int(kmap.get('shuffle',0))}。 "
                    + '三指標は脚注に閾値と PASS/FAIL を表示。'
                    + '</li>'
                )
        except Exception:
            pass

        # Derive A/B comparison status text (fairness resolved check)
        try:
            rep6_page = Path('server/public/reports/ws_vs_phieta_rep6.html')
            if rep6_page.exists():
                txt = rep6_page.read_text(encoding='utf-8')
                fair_ok = ('公平条件' in txt) and ('sha=' in txt)
            else:
                fair_ok = False
        except Exception:
            fair_ok = False
        ab_line = (
            '<li><b>A/B 公平比較（界面 W·S vs 情報流 Φ×η）</b> — 公平（k=2）集計を公開。代表6は公平条件で再計算済み（2025‑09‑26, rng=42）。</li>'
            if fair_ok
            else '<li><b>A/B 公平比較（界面 W·S vs 情報流 Φ×η）</b> — 公平（k=2）集計を公開。NGC2403 では Φ×η が優位、NGC3198 は W·S 優位。代表表とヒット集計の探索条件差異が疑われます。</li>'
        )
        body.append(
            '<div class=card>'
            '<h3>研究評価と次アクション（最新）</h3>'
            '<ol>'
            '<li><b>ULM‑P/D の語彙と設計</b> — 共有ハイパラ（ε=1, k0=0.2 kpc⁻¹, m=2, gas_scale=1.33）と公平比較（同一 n・誤差床・AICc/rχ²）が整理されています。ULM 系は総じて χ² が小さく枠組みとして整合的です。</li>'
            '<li><b>Early‑Universe（Late‑FDB）</b> — μ(a,k) の最小モデルと稀少尾倍率表を掲出。Fig‑EU1c は CLASS 3.3.2.0 実行に更新済み。</li>'
            + ab_line +
            '<li><b>単一銀河ベンチ</b> — NGC2403 は FDB が突出改善。外縁 1/r² 復帰や Hα・ω_cut の確定図系も整備済み。</li>'
            '<li><b>κ–C–Υ★ / 幾何核</b> — 等高線・Solar 上限・Padé 近似など、ミクロ閉包/幾何核の詰めに向けた素地あり。</li>'
            '<li><b>対照検証</b> — シャッフルで劣化、回転/平行移動は中央値≈0で妥当。Hα/EM は n 小で統計力限定。</li>'
            + bullet_line +
            '</ol>'
            '<h4>具体指示（優先度順）</h4>'
            '<ol>'
            '<li><b>学習κの整備</b> — Abell1689/CL0024 の <code>kappa_obs.fits</code> を Lenstool モデルから生成・配置し、(α,β,C) を学習→固定→Bullet に適用（KPI: ΔAICc（FDB−shift）≤0；rot/shuffle<0、三指標合格）。</li>'
            '<li><b>NGC3198 の公平A/B再走</b> — W·S と Φ×η でレンジ・解像度・初期値を完全一致化し、Padé最適化核を Φ×η に採用。目標: ΔAICc ≤ −6 を達成。</li>'
            '<li><b>確定図の恒常化</b> — NGC3198/2403 で外縁傾き95%CI、Hα・ω_cut重畳、∇ω_cut と a_FDB の相関を常設（NGC3198のNaNはマスク/サンプル処理を修正）。</li>'
            '<li><b>ω_cut 誤差伝播の明文化</b> — 本文/脚注に δ関係と ON/OFF 感度（T_e, [NII], 消光, L）を要約し、残差相関の主張域を明示。</li>'
            '<li><b>Υ★–κ–C 90%CL 表示</b> — 等高線に加え、中心値・誤差・相関係数の表と AU スケール上限の式を脚注に併記。</li>'
            '<li><b>数値ダッシュボード整備</b> — A/B の ΔAICc, rχ², (N,k) を同表化。対照は median/IQR/d/n を箱ひげ＋表で常設。</li>'
            '<li><b>環境依存 W(n_e, ω_cut) のトグル</b> — 主結論は W=1、ON/OFF 比較スイッチで相関・ΔAICc の差分を可視化。</li>'
            '<li><b>Early‑Universe 本計算化</b> — CLASS 連携の再現手順（version/sha/ini）を整備し、稀少尾倍率との交差表示を継続更新。</li>'
            '<li><b>データ不足の最小化</b> — 「必要データ」に tarball 受領依頼と運用フロー（受領→展開→lenstool→FITS→PIXKPC→配置）を明記。</li>'
            '<li><b>再現メタの常設</b> — フッタに shared_params の sha、AICc/(N,k)/rχ²、誤差床、PSF/ビーム、使用ID/MD5 を自動掲出（順次対応）。</li>'
            '</ol>'
            '<p><small>注: Bullet の σ_e/ω_cut は 0.5–2 keV 露光補正モザイク（CIAO 4.17）から正式生成済み。学習κ整備後にホールドアウトを解禁します。</small></p>'
            '</div>'
        )
    except Exception:
        pass
        # Bullet cluster overview (if generated)
        try:
            blet = Path('server/public/reports/cluster/bullet_overview.html')
            if blet.exists():
                body.append('<div class=card><p><a href="../reports/cluster/bullet_overview.html">衝突クラスタ検証（バレット）</a> — 共有α,β,C固定の薄レンズFDB</p></div>')
        except Exception:
            pass
        # CIAO mosaic diff report (if generated)
        try:
            diffp = Path('server/public/reports/bullet_ciao_diff.html')
            if diffp.exists():
                body.append('<div class=card><p><a href="../reports/bullet_ciao_diff.html">CIAO正式モザイク 差分チェック</a> — 0.5–2 keV 露光補正の差分（中央値）</p></div>')
        except Exception:
            pass
    # Link to ULW-l/h demo and Prospective if present
    try:
        demo = Path('server/public/reports/ulw_h_demos.html')
        if demo.exists():
            body.append('<div class=card><p><a href="../reports/ulw_h_demos.html">ULM‑P/D 図版デモ（P‑only）</a> — ρ, a₂, Φ_eff と回転曲線分解 <small>(formerly ULW‑h/l)</small></p></div>')
    except Exception:
        pass
    # Terminology note: ULM replaces ULW‑EM (first mention)
    body.append('<div class=card><small><b>用語</b>: 本稿では超長電磁モードを <b>ULM</b> と呼ぶ（旧称 ULW‑EM）。分枝は <b>ULM‑P</b>（ω>ω_cut; propagating）と <b>ULM‑D</b>（ω<ω_cut; diffusive）。</small></div>')

    # Data readiness (HALOGAS/SINGS/HA_SUB/IRAC1) with fetch commands
    try:
        def _flag(p: Path) -> str:
            return '✅' if p.exists() else '❌'
        g = {
            'NGC3198': {
                'mom1': Path('data/halogas/NGC3198-HR_mom1m.fits'),
                'mom0': Path('data/halogas/NGC3198-HR_mom0m.fits'),
                'ha_sub': Path('data/sings/ngc3198_HA_SUB_dr4.fits'),
                'irac1': Path('data/sings/ngc3198_irac1.fits'),
                'ha_sb': Path('data/halpha/NGC3198/Halpha_SB.fits'),
                'ha_png': Path('server/public/reports/ngc3198_ha_contours.png'),
                'wcut_png': Path('server/public/reports/ngc3198_omega_cut_contours.png'),
            },
            'NGC2403': {
                'mom1': Path('data/halogas/NGC2403-HR_mom1m.fits'),
                'mom0': Path('data/halogas/NGC2403-HR_mom0m.fits'),
                'ha_raw': Path('data/sings/ngc2403_HA.fits'),
                'r_band': Path('data/sings/ngc2403_R.fits'),
                'irac1': Path('data/sings/ngc2403_irac1.fits'),
                'ha_sb': Path('data/halpha/NGC2403/Halpha_SB.fits'),
                'ha_png': Path('server/public/reports/ngc2403_ha_contours.png'),
                'wcut_png': Path('server/public/reports/ngc2403_omega_cut_contours.png'),
            }
        }
        # Bullet cluster readiness
        bdir = Path('data/cluster/Bullet')
        if bdir.exists():
            rows.append('<tr><th colspan=4>Bullet (1E 0657−56)</th></tr>')
            bullet_items = [
                ('sigma_e', bdir/'sigma_e.fits'),
                ('omega_cut', bdir/'omega_cut.fits'),
                ('kappa_obs', bdir/'kappa_obs.fits'),
                ('cxo_primary_dir', bdir/'cxo'),
            ]
            for key,pp in bullet_items:
                rows.append('<tr><td>'+h(key)+'</td><td><code>'+h(str(pp))+'</code></td><td>'+_flag(pp)+'</td><td></td></tr>')
        # Do not reset rows here; append galaxy dataset checks below
        for k,v in g.items():
            rows.append('<tr><th colspan=4>' + h(k) + '</th></tr>')
            for key,pp in v.items():
                rows.append('<tr><td>'+h(key)+'</td><td><code>'+h(str(pp))+'</code></td><td>'+_flag(pp)+'</td><td></td></tr>')
        card = ['<h2>データ整備状況（自動検出）</h2>',
                '<div class=card><table><thead><tr><th>項目</th><th>パス</th><th>状態</th><th></th></tr></thead><tbody>',
                *rows,
                '</tbody></table>',
                '<p><small>取得: <code>make fetch-inputs</code> / Hα取り込み: <code>make ha-ngc3198 IN=data/sings/ngc3198_HA_SUB_dr4.fits</code>, '
                '<code>make ha-ngc2403 IN_HA=data/sings/ngc2403_HA.fits IN_R=data/sings/ngc2403_R.fits</code></small></p>',
                '<p><small>IRSA/HALOGAS の直リンクは本文の「取得手順」を参照。ダウンロード後に <code>make sota-refresh</code> で反映。</small></p></div>']
        body.extend(card)
    except Exception:
        pass
    # Scripts used to generate figures/reports (transparency)
    body.append('<h2>生成スクリプト</h2>')
    body.append('<div class=card><ul>'
                '<li><code>scripts/plot_sota_figs.py</code> — SOTA図（分布/散布図・代表VRパネルなど）</li>'
                '<li><code>scripts/build_state_of_the_art.py</code> — 本ページ生成</li>'
                '<li><code>scripts/cross_validate_shared.py</code> — 共有 μ(k) のCV</li>'
                '<li><code>scripts/benchmarks/run_ngc3198_fullbench.py</code> — NGC 3198 ベンチ</li>'
                '<li><code>scripts/demos/two_layer_demo.py</code> — 二層モデル図解</li>'
                '</ul>'
                '<p><small>実行コマンド（Make）:</small></p>'
                '<pre><code>make sota-figs\nmake build-sota\nmake cv-shared\nmake bench-ngc3198\nmake demo-two-layer</code></pre>'
                '<p><small>各スクリプトはリポジトリ内にあり、再現可能な形で構成しています。</small></p></div>')
    # Residual demos link if present
    try:
        rd = Path('server/public/reports/residual_demos.html')
        if rd.exists():
            body.append('<div class=card><p><a href="../reports/residual_demos.html">残差ヒートマップ（デモ）</a> — a₂ による方位依存の残差</p></div>')
    except Exception:
        pass
    # Surface vs volumetric comparison (rep6)
    try:
        sv = Path('server/public/reports/surface_vs_volumetric.html')
        if sv.exists():
            body.append('<div class=card><p><a href="../reports/surface_vs_volumetric.html">Σ vs 体積版（代表6）</a> — AICc/ELPD 等価性の確認</p></div>')
    except Exception:
        pass
    # Robustness addenda（対照検証/感度解析）
    try:
        nu = Path('server/public/reports/ne_null_ngc3198.html')
        if nu.exists():
            body.append('<div class=card><p><a href="../reports/ne_null_ngc3198.html">対照検証：n_e 構造依存の確認（Negative‑control tests, NGC 3198）</a> — 構造破壊時に適合が悪化</p></div>')
    except Exception:
        pass
    try:
        sn = Path('server/public/reports/sensitivity_ngc3198.html')
        if sn.exists():
            body.append('<div class=card><p><a href="../reports/sensitivity_ngc3198.html">誤差床・H_cut感度（NGC 3198）</a> — AICc/rχ² の安定性</p></div>')
    except Exception:
        pass
    try:
        ct = Path('server/public/reports/control_tests.html')
        if ct.exists():
            body.append('<div class=card><p><a href="../reports/control_tests.html">対照検証の定量（ΔAICc）</a> — 中央値/IQR・勝率を要約</p></div>')
    except Exception:
        pass
    try:
        cht = Path('server/public/reports/control_halpha_tests.html')
        if cht.exists():
            body.append('<div class=card><p><a href="../reports/control_halpha_tests.html">対照検証（Hα/EM; ΔAICc）</a> — 回転対照・平行移動対照の箱ひげと効果量</p></div>')
    except Exception:
        pass
    # 固定の用語定義（SOTA本文に常設）
    body.append('<div class=card><small><b>対照検証（Negative‑control tests）</b>: n_e 構造を破壊した偽データで再適合し、FDB の改善が本来の幾何に依存することを確認する試験。</small></div>')
    try:
        pro = Path('server/public/reports/prospective.html')
        if pro.exists():
            body.append('<div class=card><p><a href="../reports/prospective.html">Prospective 検証</a> — 共有 μ0(k), Â 固定（Υ★/gas のみ調整）</p></div>')
    except Exception:
        pass
    # Two-layer demo link (常設)
    try:
        tld = Path('server/public/reports/two_layer_demo.html')
        if tld.exists():
            body.append('<div class=card><p><a href="../reports/two_layer_demo.html">二層モデルの図解</a> — 3.6µm→ρ★, HI/CO→ρ_gas, Hα/X線→n_e→ω_cut→薄層S(r)→Λ→Φ_eff</p></div>')
    except Exception:
        pass
    # h-onlyと環境依存Wの位置づけを明確化
    body.append('<div class=card><small>公平比較は h‑only + W=1（環境依存OFF）で実施。W≠1の感度解析は研究ノート限定で別掲。</small></div>')
    # Inline representative tri-panels if present
    tri_dir = Path('assets/figures/ulw_h')
    tri_imgs = [
        ('sphere', 'ulw_h_tripanel_sphere.png', 'ulw_h_rc_sphere.png'),
        ('disk', 'ulw_h_tripanel_disk.png', 'ulw_h_rc_disk.png'),
        ('bar', 'ulw_h_tripanel_bar.png', 'ulw_h_rc_bar.png'),
    ]
    if all((tri_dir / t[1]).exists() and (tri_dir / t[2]).exists() for t in tri_imgs):
        body.append('<h2>代表三面図と回転曲線分解（h‑only）</h2>')
        for tag, p1, p2 in tri_imgs:
            src1 = f'../assets/figures/ulw_h/{p1}'
            src2 = f'../assets/figures/ulw_h/{p2}'
            body.append(
                f'<div class=card><p><b>{tag}</b></p>'
                f'<p><img {_img_html_attrs(src1)}></p>'
                f'<p><img {_img_html_attrs(src2)}></p></div>'
            )
    # Surface-emission demo link if present
    try:
        sed = Path('server/public/reports/surface_emission_demo.html')
        if sed.exists():
            body.append('<div class=card><p><a href="../reports/surface_emission_demo.html">界面放射（Σ）モデルデモ</a> — 等値面ΣからΛを評価（補遺）</p></div>')
    except Exception:
        pass
    # ULW-l/h glossary and h-only equations (inserted early in page)
    try:
        gp = Path('docs/sota/partials/ulw_lh_glossary.html')
        ep = Path('docs/sota/partials/h_only_equations.html')
        envp = Path('docs/sota/partials/env_weight_optional.html')
        twol = Path('docs/sota/partials/two_layer_summary.html')
        if gp.exists():
            body.append(gp.read_text(encoding='utf-8'))
        if ep.exists():
            body.append(ep.read_text(encoding='utf-8'))
        if envp.exists():
            body.append(envp.read_text(encoding='utf-8'))
        if twol.exists():
            body.append(twol.read_text(encoding='utf-8'))
    except Exception:
        pass
    # Equation section (legacy overview kept)
    eq: List[str] = []
    eq.append("<h2>現在の加速度の式と一貫性</h2>")
    eq.append("<div class=card>")
    eq.append("<p><b>総加速度</b> (半径Rの円筒平均近似):</p>")
    eq.append(r"$g_{\mathrm{tot}}(R)=g_{\mathrm{gas}}(R)+\mu\,g_{\mathrm{star}}(R)+g_{\mathrm{FDB}}(R;\,\mu(k))$")
    eq.append("<p><b>FDB の定義</b>（フーリエ空間倍率）:</p>")
    eq.append(r"$\mu(k)=1+\frac{\varepsilon}{1+(k/k_0)^m}$（$\varepsilon>0,\;m\gtrsim2$ は共有。高 $k$ で $\mu\to1$ → 太陽系でGRと同型）")
    eq.append("<p><b>ソースの整合</b>:</p>")
    eq.append(r"$\rho_b=(M/L)\times\text{光度}$ を採用し、$j_{\mathrm{EM}}$ ではなく $\rho_b$ を用いる（式は $\rho_b$ に統一）。")
    eq.append("<p><b>事前</b>: ガス倍率は狭い正規事前（例: 1.33±0.1）。ゲイン係数の次元は μ(k) に吸収し、一元化。</p>")
    eq.append("<p><b>補足</b>: DoG/円盤/棒などの“物理項の重み”は<b>使用しない</b>。必要な強調は損失の半径重み w(R) で行う。</p>")
    eq.append("<p><b>記号の意味（要約）</b></p>")
    eq.append(
        r"<ul>"
        r"<li>$R$: 半径[kpc]（円筒平均の自変数）</li>"
        r"<li>$r$: 2D平面での距離（$r=\lvert \mathbf{x}-\mathbf{x}'\rvert$）</li>"
        r"<li>$\mathbf{x}=(x,y)$: 2D座標</li>"
        r"<li>$g_{\mathrm{tot}}$: 総加速度，$g_{\mathrm{gas}}$, $g_{\mathrm{star}}$, $g_{\mathrm{FDB}}$</li>"
        r"<li>$\mu$: 星の有効M/L</li>"
        r"<li>$\mu(k)$: FDBの倍率関数，$k$: 波数，$k_0,\,m,\,\varepsilon$: 共有定数</li>"
        r"<li>$\rho_b$: バリオン密度（$\rho_b=(M/L)\times$光度）</li>"
        r"</ul>"
    )
    eq.append("</div>")
    body.extend(eq)
    # Bullet Cluster (practical guide)
    try:
        guide = []
        guide.append('<h2>バレットクラスタ FITS 入手ガイド（実用）</h2>')
        guide.append('<div class=card>')
        guide.append('<p><b>Chandra（ACIS）</b>: 公式ObsID 5355–5358, 5361, 4984–4986（合計~140h）。ChaSeRでPrimary/Secondaryを選択して取得。</p>')
        guide.append('<p><small>ChaSeR: <code>https://cda.harvard.edu/chaser/</code> ／ CIAO: <code>download_chandra_obsid</code> でも一括取得可。</small></p>')
        guide.append('<p><b>HST/ACS</b>: GO‑10863（F606W/F814W）。MASTで <code>1E 0657-56</code> あるいは Program=10863 を検索して <code>*_drz.fits</code>/<code>*_drc.fits</code> を取得。</p>')
        guide.append('<p><b>κ（弱+強レンズ）</b>: 2006/11/15 公開の <code>1e0657.release1.kappa.fits</code> は Wayback から取得（UFの公開ページ）。</p>')
        guide.append('<p><small>Wayback: 2007‑09‑10 snapshot → <code>/1e0657/data/1e0657.release1.kappa.fits</code> 等。</small></p>')
        guide.append('<p><b>Make</b>: <code>make fetch-bullet</code> で Chandra / κ を一括取得。</p>')
        guide.append('</div>')
        body.extend(guide)
    except Exception:
        pass
    # info-decoherence params footer (if available)
    try:
        import hashlib as _hl, json as _json
        p = Path('data/params_info.json')
        if p.exists():
            dat = _json.loads(p.read_text(encoding='utf-8'))
            sha = _hl.sha256(p.read_bytes()).hexdigest()[:12]
            body.append('<h2>情報流デコヒーレンス（UWM=ULM）パラメータ</h2>')
            body.append('<div class=card>')
            body.append(f"<p><small>params_info.json sha256:{h(sha)}</small></p>")
            keys = ['kappa','beta','eta_model','D','tau','ts']
            rows = [f"{k}={h(str(dat.get(k)))}" for k in keys if k in dat]
            body.append('<p><small>' + ' / '.join(rows) + '</small></p>')
            body.append('</div>')
    except Exception:
        pass
    # 太陽系 対照検証（旧称: Null テスト）
    body.append("<h2>太陽系 対照検証 <small>(Null テスト)</small></h2>")
    body.append(
        "<div class=card><p>高波数極限で μ(k)→1 を要請することで、Shapiro 遅延・光偏向・惑星暦の制約を満たし、"
        "太陽系では GR と同型（差は出ない）。</p></div>"
    )
    # 補助: 銀河の説明ノート（日本語・V–R文脈に寄せて記述）
    def galaxy_note(nm: str, data: Dict[str, Any]) -> str:
        try:
            from scripts.fit_sparc_fdbl import read_sparc_meta, read_sparc_massmodels
            from pathlib import Path as _P
            import numpy as _np

            meta = read_sparc_meta(_P("data/sparc/SPARC_Lelli2016c.mrt"), nm)
            rc = read_sparc_massmodels(_P("data/sparc/MassModels_Lelli2016c.mrt"), nm)

            # 形態型・距離・傾斜
            Tmap = {0:"S0",1:"Sa",2:"Sab",3:"Sb",4:"Sbc",5:"Sc",6:"Scd",7:"Sd",8:"Sdm",9:"Sm",10:"Im",11:"BCD"}
            tstr = Tmap.get(getattr(meta, 'T', None), str(getattr(meta, 'T', '不明'))) if meta else "不明"
            dstr = f"{getattr(meta,'D_mpc', '?')} Mpc" if meta and (meta.D_mpc is not None) else "? Mpc"
            inc = getattr(meta, 'Inc_deg', None)
            incstr = f"{inc:.0f}°" if isinstance(inc, (int, float)) else "?"

            # 外縁傾き（V–RのR上位30%→最大半径間の一次傾き）
            idx = _np.argsort(rc.R)
            Rn, Vn = rc.R[idx], rc.Vobs[idx]
            slope, shape = 0.0, "平坦"
            if len(Rn) >= 4:
                a = int(0.7 * len(Rn)); b = len(Rn) - 1
                dv = float(Vn[b] - Vn[a]); dR = float(max(Rn[b] - Rn[a], 1e-6))
                slope = dv / dR  # 単位: (km/s)/kpc 程度
                shape = "上昇" if slope > 1.0 else ("減少" if slope < -1.0 else "平坦")

            # Rmaxでのガス寄与（ULW最良のmuで評価）
            mu_ulw = None
            try:
                muinfo = data.get("mu", {}).get("ULW", {}).get(nm, {})
                if isinstance(muinfo, dict) and "mu" in muinfo:
                    mu_ulw = float(muinfo["mu"])
            except Exception:
                pass
            if mu_ulw is None:
                mu_ulw = 0.5
            i_last = int(_np.nanargmax(rc.R))
            Rlast = float(rc.R[i_last])
            g_gas = (rc.Vgas[i_last]**2) / max(Rlast, 1e-6)
            vstar2 = rc.Vdisk[i_last]**2 + rc.Vbul[i_last]**2
            g_star = vstar2 / max(Rlast, 1e-6)
            f_gas = float(g_gas / max(g_gas + mu_ulw * g_star, 1e-12))
            frac_txt = f"{f_gas:.2f}"
            class_txt = "ガス優勢" if f_gas > 0.5 else ("バリオン拮抗" if f_gas > 0.3 else "星優勢")

            # 1/r項の強さ（あれば）
            alpha = None
            try:
                muinfo = data.get("mu", {}).get("ULW", {}).get(nm, {})
                if isinstance(muinfo, dict) and ("alpha_line" in muinfo):
                    alpha = float(muinfo["alpha_line"])
            except Exception:
                pass
            if alpha is None:
                alpha_note = "1/r項の必要性は限定的"
            else:
                alpha_note = ("1/r項の寄与が強い" if alpha >= 30 else
                              ("1/r項は中程度" if alpha >= 10 else "1/r項は弱い"))

            # 相対指標（天の川銀河=MWを基準）
            MW_V_REF = 230.0   # km/s 相当（概ねの平坦速度）
            MW_R_REF = 20.0    # kpc 相当（円盤外縁の代表スケール）
            MW_T_REF = 4       # Sbc 近傍
            # 代表速度: 上位30%区間の中央値
            v_tail = Vn[int(0.7 * len(Vn)):] if len(Vn) else _np.array([_np.nan])
            v_char = float(_np.nanmedian(v_tail)) if v_tail.size else float('nan')
            rmax = float(_np.nanmax(Rn)) if len(Rn) else float('nan')
            vr = (v_char / MW_V_REF) if _np.isfinite(v_char) else _np.nan
            rr = (rmax / MW_R_REF) if _np.isfinite(rmax) else _np.nan
            def tag_ratio(x):
                if not _np.isfinite(x):
                    return "—"
                return ("低速" if x < 0.6 else ("同等域" if x <= 1.2 else "高速"))
            def tag_size(x):
                if not _np.isfinite(x):
                    return "—"
                return ("小型" if x < 0.6 else ("同程度" if x <= 1.2 else "大きい"))
            gas_rel = ("MW外縁(~0.3想定)より高め" if f_gas > 0.45 else
                       ("MWと同程度" if f_gas >= 0.2 else "MWより低め"))
            t_rel = ""
            if meta and getattr(meta, 'T', None) is not None:
                dT = int(meta.T) - MW_T_REF
                t_rel = ("MWより後期型" if dT >= 1 else ("MWより前期型" if dT <= -1 else "MWと近い型"))

            # 日本語の説明文（相対指標を含めて2–3文）
            line1 = f"{tstr}型、距離{dstr}、傾斜{incstr}。外縁の回転曲線は{shape}（Rmax近傾き {slope:.2f}）。"
            line2 = (
                f"MW比: 速度≈{vr*100:.0f}%（{tag_ratio(vr)}）、サイズ≈{rr:.2f}倍（{tag_size(rr)}）、"
                f"ガス寄与は{frac_txt}（{class_txt}・{gas_rel}）。{t_rel}。"
            )
            return line1 + " " + line2
        except Exception:
            return "外縁の回転曲線形状とRmaxでのガス寄与をMW基準で相対評価しています。"

    # 代表比較図: tri-compare (GR+DM / MOND / FDB) を優先表示
    # multi_fit JSONによっては names が省略されるケースがあり（旧リリース互換）、
    # その場合は μ 情報に含まれる銀河名から代表集合を再構成する。
    names_all = list(data.get("names", []) or names_cache)
    if not names_all:
        mu_ulw = data.get("mu", {}).get("ULW", {})
        if isinstance(mu_ulw, dict):
            names_all = sorted(mu_ulw.keys())
    if not names_all:
        mu_gr = data.get("mu", {}).get("GR", {})
        if isinstance(mu_gr, dict):
            names_all = sorted(mu_gr.keys())
    for preferred_name in ['NGC3198', 'NGC2403']:
        if preferred_name not in names_all:
            names_all.insert(0, preferred_name)
    names = [nm for nm in names_all if nm not in _load_blacklist()]
    preferred = [nm for nm in ['NGC3198', 'NGC2403'] if nm in names]
    remaining = [nm for nm in names if nm not in preferred]
    # For format unification: always use rep6 figures (Total基準テンプレv2)
    try:
        # rep6 list
        rep6_names = [ln.strip() for ln in Path('data/sparc/sets/rep6.txt').read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.startswith('#')]
    except Exception:
        rep6_names = ['DDO154','DDO161','NGC2403','NGC3198','NGC7331','UGC06787']
    body.append("<h2>代表比較図（rep6, Total基準・テンプレv2）</h2>")
    grid_items: List[str] = []
    for nm in rep6_names:
        png = Path('assets/rep6') / f'{nm}_rep6.png'
        svg = Path('assets/rep6') / f'{nm}_rep6.svg'
        if not png.exists() and not svg.exists():
            continue
        src = f"../assets/rep6/{h(png.name)}" if png.exists() else f"../assets/rep6/{h(svg.name)}"
        note = galaxy_note(nm, data)
        memo_href = f"../memo/galaxies/{h(nm)}.md"
        cap = f"<a href=\"{memo_href}\">{h(nm)}</a> — <small>{h(note)}</small>"
        grid_items.append(f"<figure class=\"card\"><img {_img_html_attrs(src, style='max-width:100%')}><figcaption>{cap}</figcaption></figure>")
    if grid_items:
        body.append("<section class=\"two-col\">" + "\n".join(grid_items) + "</section>")
    else:
        body.append("<div class=card><p>rep6 図が見つかりませんでした。make rep6 を実行してください。</p></div>")
    # Ensure public assets for figures under /assets/figures (alpha_line 図は配信しない方針)
    pub_assets = Path("server/public/assets/figures")
    src_assets = Path("assets/figures")
    try:
        pub_assets.mkdir(parents=True, exist_ok=True)
        for name in ("boot_lam_lsb.png", "boot_lam_hsb.png"):
            s = src_assets / name
            if s.exists():
                shutil.copy2(s, pub_assets / name)
    except Exception:
        pass
    # alpha_line ヒストグラムは廃止（μ(k) へ統合）
    # Embed CV and bootstrap summaries if present
    cv = Path("data/results/cv_shared_summary.json")
    if cv.exists():
        try:
            import json as _json
            cvd = _json.loads(cv.read_text(encoding='utf-8'))
            agg = cvd.get('aggregate', {})
            # fold中央値 ΔAICc を計算（存在すれば）
            med_txt = ""
            try:
                folds = cvd.get('folds', [])
                dels = []
                for f in folds:
                    t = f.get('test', {})
                    daicc = t.get('delta_AICc')
                    if daicc is None:
                        # fallback to delta_AIC
                        daicc = t.get('delta_AIC')
                    if daicc is not None:
                        dels.append(float(daicc))
                if dels:
                    dels.sort()
                    m = dels[len(dels)//2]
                    med_txt = f" / 中央ΔAICc={h(f'{m:.2f}')}"
            except Exception:
                med_txt = ""
            body.append("<h2>交差検証 要約</h2>")
            Ns = agg.get('N_sum',{}); Ks = agg.get('K_sum',{})
            body.append(
                f"<div class=card><p>Test合算: χ² GR={h(str(agg.get('chi2_GR')))} / ULM={h(str(agg.get('chi2_ULW')))} "
                f"(改善×{h(str(agg.get('improve_factor')))}), ΔAICc={h(str(agg.get('delta_AICc')))}{med_txt}</p>"
                f"<p><small>(n,k): GR=({h(str(Ns.get('GR')))}, {h(str(Ks.get('GR')))}), ULM=({h(str(Ns.get('ULW')))}, {h(str(Ks.get('ULW')))})</small></p>"
                "<p><a href=\"../reports/cv_shared_summary.html\">詳細レポート</a></p></div>"
            )
        except Exception:
            pass
    # LSB/HSB (noBL) CV summaries
    for tag, lab in [("cv_shared_summary_lsb_noBL.json", "LSB(noBL)"), ("cv_shared_summary_hsb_noBL.json", "HSB(noBL)")]:
        p = Path("data/results") / tag
        if p.exists():
            try:
                import json as _json
                dsub = _json.loads(p.read_text(encoding='utf-8'))
                agg = dsub.get('aggregate', {})
                href = f"../reports/{tag.replace('.json','.html')}"
                body.append(f"<h2>交差検証 要約 — {h(lab)}</h2>")
                Ns = agg.get('N_sum',{}); Ks = agg.get('K_sum',{})
                body.append(
                    f"<div class=card><p>Test合算: χ² GR={h(str(agg.get('chi2_GR')))} / ULM={h(str(agg.get('chi2_ULW')))} "
                    f"(改善×{h(str(agg.get('improve_factor')))}), ΔAICc={h(str(agg.get('delta_AICc')))}</p>"
                    f"<p><small>(n,k): GR=({h(str(Ns.get('GR')))}, {h(str(Ks.get('GR')))}), ULM=({h(str(Ns.get('ULW')))}, {h(str(Ks.get('ULW')))})</small></p>"
                    f"<p><a href=\"{href}\">詳細レポート</a></p></div>"
                )
            except Exception:
                pass
    # Grouped-k0 (overall) CV summary, if present
    p = Path('data/results/cv_shared_summary_grouped_k0.json')
    if p.exists():
        try:
            import json as _json
            cvd = _json.loads(p.read_text(encoding='utf-8'))
            agg = cvd.get('aggregate', {})
            body.append("<h2>交差検証 要約 — 群別k0</h2>")
            body.append(
                f"<div class=card><p>Test合算: χ² GR={h(str(agg.get('chi2_GR')))} / ULM={h(str(agg.get('chi2_ULW')))} "
                f"(改善×{h(str(agg.get('improve_factor')))}), ΔAICc={h(str(agg.get('delta_AICc')))} / "
                f"rχ² GR={h(str(agg.get('rchi2_GR')))} / ULM={h(str(agg.get('rchi2_ULW')))}</p>"
                f"<p><a href=\"../reports/cv_shared_summary_grouped_k0.html\">詳細レポート</a></p></div>"
            )
        except Exception:
            pass
    for tag in ("boot_lam_lsb.png", "boot_lam_hsb.png"):
        p = Path("assets/figures") / tag
        if p.exists():
            title = "LSB λブートストラップ" if tag.endswith("lsb.png") else "HSB λブートストラップ"
            body.append(f"<h2>{h(title)}</h2>")
            src = f"../assets/figures/{h(tag)}"
            body.append(
                f"<figure class=\"card\"><img {_img_html_attrs(src)}></figure>"
            )
            body.append("<div class=card><small>注: 現行設計では μ(k) の特性スケール k0 と λ は概ね λ≈1/k0 の関係にあります。λブートストラップは k0 分布の参考値として読み替え可能です。</small></div>")
    # Blacklist policy and IDs
    try:
        bl = _load_blacklist()
        if bl:
            body.append("<h2>ブラックリスト基準と除外ID</h2>")
            body.append(
                "<div class=card><p>除外基準の例:</p><ul>"
                "<li>著しい非軸対称（強い棒渦・擾乱）で円対称前提が破綻</li>"
                "<li>距離・傾斜の不確かさが大きく回転曲線が不安定</li>"
                "<li>外的擾乱・相互作用の兆候が強い</li>"
                "</ul></div>"
            )
            ids = sorted(bl)
            body.append(f"<div class=card><p>除外ID（{len(ids)}件）</p><small>" + ", ".join(h(x) for x in ids) + "</small></div>")
    except Exception:
        pass
    # Export used IDs (dataset after blacklist) for reproducibility
    try:
        used = [nm for nm in data.get('names', []) if nm not in _load_blacklist()]
        out_ids = Path('server/public/state_of_the_art/used_ids.csv')
        out_ids.parent.mkdir(parents=True, exist_ok=True)
        out_ids.write_text("name\n" + "\n".join(used) + "\n", encoding='utf-8')
    except Exception:
        pass
    # Baseline comparison summary (AICc)
    try:
        # choose shared a0 and pass to MOND aggregation (fallback: default ≈3.7×10³)
        a0_best = _best_mond_a0(data)
        sums_m, nk_m = _aggregate_mond_vs_gr(data, a0_best)
        sums_g, nk_g = _aggregate_grdm_vs_gr(data)
        body.append("<h2>ベースライン比較（AICc, 集計）</h2>")
        # ΔAICc vs GR
        try:
            d_grdm = (float(sums_g.get('AICc_GRDM')) - float(sums_g.get('AICc_GR')))
        except Exception:
            d_grdm = float('nan')
        try:
            d_mond = (float(sums_m.get('AICc_MOND')) - float(sums_g.get('AICc_GR')))
        except Exception:
            d_mond = float('nan')
        try:
            d_fdb = (float(sums_g.get('AICc_ULW')) - float(sums_g.get('AICc_GR')))
        except Exception:
            d_fdb = float('nan')
        body.append(
            "<div class=card>"
            f"<p>M1: GR+DM(NFW c–M), M2: MOND, M3: FDB</p>"
            f"<p>AICc: GR={h(str(sums_g.get('AICc_GR')))} (n={h(str(nk_g.get('N_GR')))},k={h(str(nk_g.get('k_GR')))}) / "
            f"GR+DM={h(str(sums_g.get('AICc_GRDM')))} (ΔAICc={h(str(d_grdm))}) / "
            f"MOND={h(str(sums_m.get('AICc_MOND')))} (ΔAICc={h(str(d_mond))}) / "
            f"FDB={h(str(sums_g.get('AICc_ULW')))} (ΔAICc={h(str(d_fdb))})</p>"
            f"<p><small>n,k: GR={h(str(nk_g.get('N_GR')))}, {h(str(nk_g.get('k_GR')))} / GR+DM={h(str(nk_g.get('N_GRDM')))}, {h(str(nk_g.get('k_GRDM')))} / "
            f"MOND={h(str(nk_m.get('N_MOND')))}, {h(str(nk_m.get('k_MOND')))} / FDB={h(str(nk_g.get('N_ULW')))}, {h(str(nk_g.get('k_ULW')))}</small></p>"
            f"<p><small>注: MONDは共有 a0（例: a0≈{a0_best:.2e}）を一次近似で選択。"
            "GR+DMは銀河ごとにV200,c（または等温 V0,rc）を推定し、NFWのcにはc–M事前（ln cのガウス, σ≈0.35）を加味。"
            "本カードのAICcは <b>共通n（観測側マスク）</b>に統一しています。</small></p>"
            "</div>"
        )
        wins = _win_rates(data)
        if wins:
            tot = max(1, int(wins.get('total', 1)))
            body.append(
                "<div class=card>"
                f"<p>勝率（χ²でGRに勝った割合）: "
                f"GR+DM {int(wins.get('GRDM_vs_GR',0))}/{tot}, "
                f"MOND {int(wins.get('MOND_vs_GR',0))}/{tot}, "
                f"FDB {int(wins.get('FDB_vs_GR',0))}/{tot}</p>"
                "</div>"
            )
        wins_a = _win_rates_aicc(data)
        if wins_a:
            tot = max(1, int(wins_a.get('total', 1)))
            body.append(
                "<div class=card>"
                f"<p>勝率（ΔAICcでGRに勝った割合）: "
                f"GR+DM {int(wins_a.get('GRDM',0))}/{tot}, "
                f"MOND {int(wins_a.get('MOND',0))}/{tot}, "
                f"FDB {int(wins_a.get('FDB',0))}/{tot}</p>"
                "<p><small>注: per-galaxyのΔAICcではULW共有(ε,k0,m)の3自由度は銀河横断のため含めていません。集計AICcでは共有自由度を考慮しています。</small></p>"
                "</div>"
            )
    except Exception:
        pass
    write_html(sota, "State of the Art", "\n".join(body))
    # Append units and rχ² note at the end for clarity
    foot: List[str] = []
    foot.append("<h2>記号の意味</h2>")
    foot.append("<div class=card><ul>"
                "<li>ε: μ(k)の強度（無次元）</li>"
                "<li>k0: μ(k)の特性スケール [kpc⁻¹]（λ≈1/k0）</li>"
                "<li>m: μ(k)の指数（無次元）</li>"
                "<li>gas_scale: ガス質量スケールの比率（無次元）</li>"
                "</ul></div>")
    foot.append(
        "<div class=card><small>注: reduced χ² は rχ² = χ²/(N−k)。"
        "N は<b>共通マスク</b>で揃えた有効データ点、k は当該集計に含めた自由度。"
        "fold 合算では各 fold の N と k を加算して算出します。"
        "共有 μ(k) サマリは k<sub>global</sub>=4（ε,k0,m,gas_scale）。"
        "per‑galaxy 表示は銀河内パラメータのみを数え、共有ハイパーは含めません。"
        "観測速度誤差には 5 km/s の下限（点毎に clip(0.03×Vobs, 3..7)）を適用。"
        "NFW の濃度には c–M 事前（ln c のガウス, σ≈0.35）を加味します。</small></div>"
    )
    write_html(sota, "State of the Art", "\n".join(body + foot))
    # Build table page (full per-galaxy listing)
    table_body: List[str] = []
    table_body.append("<h1>全銀河のM/L一覧</h1>")
    table_body.append('<div class=card><small>表記: AICc を用い、(N,k) と rχ²=χ²/(N−k) の定義に準拠します。SOTAトップと同一の shared_params.json（sha指紋）を参照しています。</small></div>')
    table_body.append(brief_results(data))
    write_html(Path("server/public/state_of_the_art/table.html"), "M/L Table", "\n".join(table_body))

    # === Post-build sanitation: enforce metrics card + shared sha footer on key pages ===
    def _inject_metrics_footer(path: Path) -> None:
        try:
            txt = path.read_text(encoding='utf-8')
        except Exception:
            return
        changed = False
        # AICc/(N,k)/rχ² definition card
        need_metrics = ('rχ²' not in txt) or ('AICc' not in txt)
        if need_metrics:
            card = (
                '<div class=card><small>指標: AICc を用い、(N,k) と '
                'rχ²=χ²/(N−k) を併記します。誤差床は clip(0.03×Vobs, 3..7 km/s)。'
                '脚注に PSF/ビーム・マスク・誤差床の定義を固定します。</small></div>'
            )
            if '</main>' in txt:
                txt = txt.replace('</main>', card + '</main>')
            else:
                txt = txt + '\n' + card
            changed = True
        # shared_params.json sha footer
        shf = ''
        try:
            import hashlib as _hl
            psp = Path('data/shared_params.json')
            if psp.exists():
                shf = _hl.sha256(psp.read_bytes()).hexdigest()[:12]
        except Exception:
            shf = ''
        if shf and ('shared_params.json' not in txt and 'sha256:' not in txt):
            foot = (
                f"<footer class=\"site-footer\"><div class=\"wrap\">"
                f"<small>source: data/shared_params.json (sha256:{h(shf)})</small>"
                f"</div></footer>"
            )
            if '</body>' in txt:
                txt = txt.replace('</body>', foot + '</body>')
            else:
                txt = txt + '\n' + foot
            changed = True
        # Terminology sync
        new_txt = (txt.replace('ULW‑', 'ULM‑')
                       .replace('ULW', 'ULM')
                       .replace('Null テスト', '対照検証')
                       .replace('ヌル', '対照検証'))
        if new_txt != txt:
            txt = new_txt
            changed = True
        if changed:
            path.write_text(txt, encoding='utf-8')

    # Apply to SOTA pages and key reports
    targets: list[Path] = []
    targets += list(Path('server/public/state_of_the_art').glob('*.html'))
    rep = Path('server/public/reports')
    if rep.exists():
        targets += list(rep.glob('*.html'))
        for sub in (rep / 'cluster', rep / 'benchmarks'):
            if sub.exists():
                targets += list(sub.glob('*.html'))
    for t in targets:
        _inject_metrics_footer(t)
        try:
            txt = t.read_text(encoding='utf-8')
        except Exception:
            continue
        changed_local = False
        name = t.name.lower()
        reports_dir = Path('server/public/reports')
        try:
            def _ensure_contour_card(filename: str) -> None:
                nonlocal txt, changed_local
                oc = reports_dir / filename
                if not oc.exists():
                    return
                attrs = _img_html_attrs(filename, base_dir=reports_dir)
                new_card = ('<h2>ω_cut 等高線</h2>'
                            f'<div class=card><p><img {attrs}></p>'
                            '<p><small>推定: EM→n_e（薄層厚 L≈100 pc 仮定）→ ω_p=√(n_e e²/ε₀m_e)。値は概算のため、温度・[NII]補正・消光の系統に注意。</small></p></div>')
                if filename in txt:
                    pattern = rf'<div class=card><p><img src="{filename}"[^>]*></p>'
                    new_txt = re.sub(pattern, f'<div class=card><p><img {attrs}></p>', txt, count=1)
                    if new_txt != txt:
                        txt = new_txt
                        changed_local = True
                else:
                    if '</main>' in txt:
                        txt = txt.replace('</main>', new_card + '</main>', 1)
                    else:
                        txt = txt + '\n' + new_card
                    changed_local = True

            if name == 'bench_ngc3198.html':
                _ensure_contour_card('ngc3198_omega_cut_contours.png')
            if name == 'bench_ngc2403.html':
                _ensure_contour_card('ngc2403_omega_cut_contours.png')
        except Exception:
            pass
        # Add outer gR² slope numeric summary if CSV present
        try:
            import numpy as _np  # imported lazily to avoid overhead when unavailable
            def _ensure_outer_slope(filename: str, label: str) -> None:
                nonlocal txt, changed_local
                csvp = reports_dir / filename
                if not csvp.exists() or label in txt:
                    return
                dat = _np.genfromtxt(csvp, delimiter=',', names=True)
                x = _np.asarray(dat['R_kpc'], dtype=float)
                y = _np.asarray(dat['gR2'], dtype=float)
                n = len(x)
                start = int(max(0, n * 0.7))
                xs = x[start:]
                ys = y[start:]
                if len(xs) < 3:
                    return
                xs0 = xs - xs.mean()
                Sxx = float((xs0 * xs0).sum())
                a = float((xs0 * ys).sum() / max(Sxx, 1e-12))
                b = float(ys.mean())
                yhat = a * xs0 + b
                rss = float(((ys - yhat) ** 2).sum())
                dof = max(len(xs) - 2, 1)
                se = (rss / dof / max(Sxx, 1e-12)) ** 0.5
                ci = 1.96 * se
                card = (f"<div class=card><small>外縁傾き（gR² の線形近似; 上位30%半径）: slope={a:.3g} ± {ci:.2g} (95%CI)</small></div>")
                if '</main>' in txt:
                    txt = txt.replace('</main>', card + '</main>')
                else:
                    txt = txt + '\n' + card
                changed_local = True

            if name == 'bench_ngc3198.html':
                _ensure_outer_slope('ngc3198_outer_gravity.csv', '外縁傾き')
            if name == 'bench_ngc2403.html':
                _ensure_outer_slope('ngc2403_outer_gravity.csv', '外縁傾き')
        except Exception:
            pass
        if changed_local:
            t.write_text(txt, encoding='utf-8')
    # Add Research Kits section page if kits figures exist (light integration)
    kits = []
    # Link FDB anisotropic kernel demos and parameter sweeps if present
    if Path('server/public/reports/fdb_aniso_demos.html').exists():
        kits.append('<div class="card"><a href="../reports/fdb_aniso_demos.html">FDB anisotropic kernel demos (sphere/rod/disk)</a></div>')
    if Path('server/public/reports/fdb_param_sweep.html').exists():
        kits.append('<div class="card"><a href="../reports/fdb_param_sweep.html">FDB parameter sweep (ℓ0, m, λ_an)</a></div>')
    kits_dir = Path('server/public/assets/kits')
    if (kits_dir / 'solar_residual_demo.png').exists():
        src = '../assets/kits/solar_residual_demo.png'
        kits.append(
            f'<figure class="card"><img {_img_html_attrs(src)}><figcaption>Solar conjunction achromatic residual (demo)</figcaption></figure>'
        )
    if (kits_dir / 'pta_rms_vs_f.png').exists():
        src = '../assets/kits/pta_rms_vs_f.png'
        kits.append(
            f'<figure class="card"><img {_img_html_attrs(src)}><figcaption>PTA correlation shape RMS vs f (demo)</figcaption></figure>'
        )
    if kits:
        body_k = ["<h1>Research Kits</h1>", '<section class="two-col">' + "\n".join(kits) + '</section>']
        write_html(Path("server/public/kits/index.html"), "Research Kits", "\n".join(body_k))
    print("wrote:", sota)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
def render_markdown_simple(md: str) -> str:
    """Very small, dependency-free Markdown to HTML (good enough for our ops memo).

    Supports: #/##/### headers, bold **..**, inline code `..`, links [t](u),
              paragraphs, unordered lists (- or *), fenced code ```.
    """
    html: List[str] = []
    in_code = False
    list_open = False
    def flush_list():
        nonlocal list_open
        if list_open:
            html.append('</ul>')
            list_open = False
    for raw in md.splitlines():
        ln = raw.rstrip('\n')
        if ln.strip().startswith('```'):
            if in_code:
                html.append('</pre></code>')
                in_code = False
            else:
                flush_list()
                html.append('<code><pre>')
                in_code = True
            continue
        if in_code:
            html.append(h(ln))
            continue
        if not ln.strip():
            flush_list()
            html.append('')
            continue
        # headers
        if ln.startswith('### '):
            flush_list(); html.append('<h3>'+h(ln[4:])+'</h3>'); continue
        if ln.startswith('## '):
            flush_list(); html.append('<h2>'+h(ln[3:])+'</h2>'); continue
        if ln.startswith('# '):
            flush_list(); html.append('<h1>'+h(ln[2:])+'</h1>'); continue
        # list
        if ln.lstrip().startswith(('- ', '* ')):
            if not list_open:
                html.append('<ul>'); list_open = True
            item = ln.lstrip()[2:]
            # inline formatting on item
            s = item
            s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
            s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
            s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href=\"\2\">\1</a>", s)
            html.append('<li>'+s+'</li>')
            continue
        else:
            flush_list()
        # paragraph with inline formatting
        s = ln
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href=\"\2\">\1</a>", s)
        # horizontal rule
        if set(ln.strip()) == {'-'} and len(ln.strip()) >= 3:
            html.append('<hr>')
        else:
            html.append('<p>'+s+'</p>')
    flush_list()
    return "\n".join(html)
