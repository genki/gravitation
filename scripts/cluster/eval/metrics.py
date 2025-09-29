#!/usr/bin/env python3
from __future__ import annotations
import json
import numpy as np
from pathlib import Path


def peak_xy(a: np.ndarray) -> tuple[int, int]:
    idx = int(np.nanargmax(a))
    ny, nx = a.shape
    y, x = divmod(idx, nx)
    return y, x


def main() -> int:
    # Load observed and model κ maps if present; otherwise compare model internals
    # Prefer using observed grid size for both model and sigma
    obs_path = Path('data/cluster/bullet/kappa.npy')
    mod = np.load('data/cluster/fdb/bullet_kappa_fdb.npy')
    if obs_path.exists():
        obs = np.load(obs_path)
    else:
        obs = mod  # fallback
    # Resample model to observed if needed
    if mod.shape != obs.shape:
        import scipy.ndimage as ndi
        zy, zx = obs.shape[0]/mod.shape[0], obs.shape[1]/mod.shape[1]
        mod = ndi.zoom(mod, zoom=(zy, zx), order=1)
    # X-ray proxy peak from Σ_e
    sigma_p = Path('data/cluster/maps/bullet_sigma_e_kappa.npy')
    sigma = np.load(sigma_p) if sigma_p.exists() else np.load('data/cluster/maps/bullet_sigma_e.npy')
    if sigma.shape != obs.shape:
        import scipy.ndimage as ndi
        zy, zx = obs.shape[0]/sigma.shape[0], obs.shape[1]/sigma.shape[1]
        sigma = ndi.zoom(sigma, zoom=(zy, zx), order=1)
    # galaxy/ICL proxy peak (placeholder zeros)
    gal = np.zeros_like(mod)
    # Peaks
    py_m, px_m = peak_xy(mod)
    py_x, px_x = peak_xy(sigma)
    py_g, px_g = peak_xy(gal)
    # Offsets
    dx_pix_mx = float(np.hypot(px_m - px_x, py_m - py_x))
    dx_pix_mg = float(np.hypot(px_m - px_g, py_m - py_g))
    # Convert to kpc if scale provided
    scale = None
    p = Path('data/cluster/params_cluster.json')
    if p.exists():
        try:
            scale = float((json.loads(p.read_text(encoding='utf-8')).get('scale_kpc_per_pix')))
        except Exception:
            scale = None
    dx_kpc_mx = (dx_pix_mx * scale) if scale else None
    dx_kpc_mg = (dx_pix_mg * scale) if scale else None
    out = {
        'peak_model': {'y': py_m, 'x': px_m},
        'peak_xray': {'y': py_x, 'x': px_x},
        'peak_gal': {'y': py_g, 'x': px_g},
        'offset_model_xray_pix': dx_pix_mx,
        'offset_model_gal_pix': dx_pix_mg,
        'scale_kpc_per_pix': scale,
        'offset_model_xray_kpc': dx_kpc_mx,
        'offset_model_gal_kpc': dx_kpc_mg,
    }
    # AICc on pixels (unweighted proxy) for GR/FDB/TOT vs observed kappa
    try:
        kappa_gr = np.load('data/cluster/gr/bullet_kappa_gr.npy')
        if kappa_gr.shape != obs.shape:
            import scipy.ndimage as ndi
            zy, zx = obs.shape[0]/kappa_gr.shape[0], obs.shape[1]/kappa_gr.shape[1]
            kappa_gr = ndi.zoom(kappa_gr, zoom=(zy, zx), order=1)
    except Exception:
        kappa_gr = np.zeros_like(obs)
    try:
        kappa_fdb = np.load('data/cluster/fdb/bullet_kappa_fdb.npy')
        if kappa_fdb.shape != obs.shape:
            import scipy.ndimage as ndi
            zy, zx = obs.shape[0]/kappa_fdb.shape[0], obs.shape[1]/kappa_fdb.shape[1]
            kappa_fdb = ndi.zoom(kappa_fdb, zoom=(zy, zx), order=1)
    except Exception:
        kappa_fdb = np.zeros_like(obs)
    kappa_tot = kappa_gr + kappa_fdb
    m = np.isfinite(obs)
    N = int(np.sum(m)) if np.sum(m) > 0 else obs.size
    def aicc(chi2: float, k: int, N: int) -> float:
        return float(chi2 + (2*k*(k+1))/max(N-k-1,1))
    chi_gr = float(np.nansum((kappa_gr[m]-obs[m])**2))
    chi_fdb = float(np.nansum((kappa_fdb[m]-obs[m])**2))
    chi_tot = float(np.nansum((kappa_tot[m]-obs[m])**2))
    out['AICc'] = {
        'GR': aicc(chi_gr, 0, N),
        'FDB': aicc(chi_fdb, 0, N),
        'TOT': aicc(chi_tot, 0, N),
        'N': N,
        'k': {'GR': 0, 'FDB': 0, 'TOT': 0}
    }
    out['delta_AICc'] = {
        'TOT_minus_GR': out['AICc']['TOT'] - out['AICc']['GR'],
        'TOT_minus_FDB': out['AICc']['TOT'] - out['AICc']['FDB'],
        'FDB_minus_GR': out['AICc']['FDB'] - out['AICc']['GR']
    }
    Path('server/public/reports/cluster').mkdir(parents=True, exist_ok=True)
    Path('server/public/reports/cluster/bullet_metrics.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('wrote metrics:', 'server/public/reports/cluster/bullet_metrics.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
