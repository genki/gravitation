#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from scripts.fit_sparc_fdbl import read_sparc_massmodels
from scripts.compare_fit_multi import to_accel, line_bias_accel, chi2
from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_profile_from_map
from astropy.io import fits


def with_error_floor(R, Vobs, eV):
    Vobs = np.asarray(Vobs, float); eV = np.asarray(eV, float)
    floor = np.clip(0.03*np.abs(Vobs), 3.0, 7.0)
    eVe = np.sqrt(np.maximum(eV,1e-6)**2 + floor**2)
    return to_accel(R, Vobs, eVe)


def load_ha_or_proxy(name: str):
    p = Path(f'data/halpha/{name}/Halpha_SB.fits')
    if p.exists():
        img = fits.getdata(p).astype(float)
        hdr = fits.getheader(p)
        pix = float(hdr.get('PIXSCALE', 0.305)) / 206265.0 * 1.0
        if not np.isfinite(pix) or pix <= 0:
            pix = 0.2
        return img, pix
    # fallback: symmetric
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    from scripts.fit_sparc_fdbl import make_axisymmetric_image
    return make_axisymmetric_image(rc.R, rc.SBdisk, pix_kpc=0.2, size=256), 0.2


def profile(name: str) -> str:
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    R = rc.R; g_gas = (1.33*(rc.Vgas*rc.Vgas))/np.maximum(R,1e-6); g_star0 = (rc.Vdisk*rc.Vdisk+rc.Vbul*rc.Vbul)/np.maximum(R,1e-6)
    g_obs, eg = with_error_floor(R, rc.Vobs, rc.eV)
    img, pix = load_ha_or_proxy(name)
    k_grid = np.linspace(0.02, 1.0, 20); phi_k = np.exp(-(k_grid/0.6)**2)
    g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k, eta_params=EtaParams(beta=0.3, s_kpc=0.5))
    m = np.isfinite(g_obs)&np.isfinite(eg)&np.isfinite(g_gas)&np.isfinite(g_star0)&np.isfinite(g_if)
    # Solve LS for [mu,kappa]
    def fit(mu0=0.7, k0=1.0):
        mb = m
        w = 1.0/np.maximum(eg[mb],1e-6)
        X1 = g_star0[mb]; X2 = g_if[mb]
        Y  = g_obs[mb] - g_gas[mb]
        S11 = float(np.nansum(w*X1*X1)); S22 = float(np.nansum(w*X2*X2)); S12 = float(np.nansum(w*X1*X2))
        b1  = float(np.nansum(w*X1*Y));   b2  = float(np.nansum(w*X2*Y))
        det = S11*S22 - S12*S12
        if det <= 0: return mu0, k0
        mu = (b1*S22 - b2*S12) / det
        k  = (S11*b2 - S12*b1) / det
        return float(mu), float(k)
    mu_hat, k_hat = fit()
    # Grid around the optimum
    mu_grid = np.linspace(max(0, mu_hat-0.6), mu_hat+0.6, 41)
    k_grid2 = np.linspace(max(0, k_hat-2.0), k_hat+2.0, 41)
    chi0 = None
    Z = np.empty((len(mu_grid), len(k_grid2)))
    for i, mu in enumerate(mu_grid):
        for j, k in enumerate(k_grid2):
            gmod = g_gas + mu*g_star0 + k*g_if
            val = chi2(g_obs[m], eg[m], gmod[m])
            if chi0 is None: chi0 = val
            Z[i,j] = val
    dchi = Z - np.nanmin(Z)
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1,1, figsize=(5.0,4.0))
    cs = ax.contour(k_grid2, mu_grid, dchi, levels=[2.30, 6.18, 11.83], colors=('C0','C1','C2'))
    ax.clabel(cs, fmt=lambda v: f"Δχ²={v:.2f}", fontsize=8)
    ax.axvline(k_hat, ls='--', color='k', lw=0.8); ax.axhline(mu_hat, ls='--', color='k', lw=0.8)
    ax.set_xlabel('κ (追加項スケール)'); ax.set_ylabel('Υ★')
    ax.set_title(f'{name}: プロフィール尤度（μ, κ）')
    out = Path('server/public/reports')/f'{name.lower()}_profile_mu_kappa.png'
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
    return str(out)


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='Make profile-likelihood plots for (mu, kappa)')
    ap.add_argument('--names', type=str, default='NGC3198,NGC2403')
    args = ap.parse_args()
    names = [n.strip() for n in args.names.split(',') if n.strip()]
    outs = [profile(nm) for nm in names]
    for p in outs: print('wrote', p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

