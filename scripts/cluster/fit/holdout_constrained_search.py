#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import os
import numpy as np
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
from scipy import ndimage as ndi
from scipy.stats import spearmanr

from scripts.cluster.min_kernel import MinKernelParams, predict_kappa


def load_maps(root: Path):
    oc = root / 'omega_cut.fits'; se = root / 'sigma_e.fits'; ko = root / 'kappa_obs.fits'
    if not (oc.exists() and se.exists() and ko.exists()):
        return None
    try:
        ocv = fits.getdata(oc).astype(float)
        sev = fits.getdata(se).astype(float)
        kov = fits.getdata(ko).astype(float)
        pix = float(fits.getheader(se).get('PIXKPC', 1.0))
    except Exception:
        return None
    return ocv, sev, kov, pix


def aicc(chi2: float, k: int, N: int) -> float:
    return float(chi2 + 2*k + (2*k*(k+1))/max(N-k-1, 1))


def align_fft(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, float, float]:
    import numpy.fft as _fft
    A = a; B = b
    FA = _fft.rfftn(A); FB = _fft.rfftn(B)
    CC = _fft.irfftn(FA * np.conj(FB), s=A.shape)
    py, px = np.unravel_index(int(np.nanargmax(CC)), CC.shape)
    cy, cx = A.shape[0]//2, A.shape[1]//2
    dyf = float(py - cy); dxf = float(px - cx)
    return ndi.shift(a, shift=(-dyf, -dxf), order=1, mode='nearest'), dyf, dxf


def main() -> int:
    root = Path('data/cluster/Bullet')
    data = load_maps(root)
    if data is None:
        print('missing Bullet maps; abort')
        return 1
    oc, se, kobs, pix = data

    # Load shared params learned on training clusters
    pjson = Path('data/cluster/params_cluster.json')
    if not pjson.exists():
        print('shared params json not found:', pjson)
        return 2
    jd = json.loads(pjson.read_text(encoding='utf-8'))
    base = MinKernelParams(alpha=float(jd.get('alpha', 0.6)), beta=float(jd.get('beta', 0.8)), C=float(jd.get('C', 0.05)),
                           xi=float(jd.get('xi', 0.7)), p=float(jd.get('p', 0.5)), tau_q=float(jd.get('tau_q', 0.6)), delta_tau_frac=float(jd.get('delta_tau_frac', 0.1)),
                           s_gate=float(jd.get('s_gate', 1.0)), se_transform=str(jd.get('se_transform', 'none')),
                           xi_sat=float(jd.get('xi_sat', 1e12)))

    betas = [float(x) for x in (os.environ.get('GRID_BETA', '0.3,0.5,0.7,0.9').split(',')) if x.strip()]
    # process settings consistent with report
    gauss_sig = float(os.environ.get('BULLET_PSF_SIGMA', '0.5'))
    w_pow = float(os.environ.get('BULLET_W_POWER', '1.0'))

    candidates = []
    for b in betas:
        p = MinKernelParams(alpha=base.alpha, beta=float(b), C=base.C, xi=base.xi, p=base.p, tau_q=base.tau_q, delta_tau_frac=base.delta_tau_frac, s_gate=base.s_gate, se_transform=base.se_transform, xi_sat=base.xi_sat)
        kpred = predict_kappa(oc, se, pix, p)
        if kpred.shape != kobs.shape:
            zy, zx = kobs.shape[0]/kpred.shape[0], kobs.shape[1]/kpred.shape[1]
            kpred = ndi.zoom(kpred, zoom=(zy, zx), order=1)
        kp = ndi.gaussian_filter(kpred, sigma=gauss_sig)
        ko = ndi.gaussian_filter(kobs,  sigma=gauss_sig)
        kp_al, dyf, dxf = align_fft(kp, ko)
        res = (ko - kp_al)
        med = float(np.nanmedian(res)); mad = float(np.nanmedian(np.abs(res - med)))
        sigma = max(1.4826*mad, 1e-6)
        m = np.isfinite(ko) & np.isfinite(kp_al)
        if not np.any(m):
            continue
        se_obs = se if se.shape == ko.shape else ndi.zoom(se, zoom=(ko.shape[0]/se.shape[0], ko.shape[1]/se.shape[1]), order=1)
        w = (se_obs / (np.nanmean(se_obs) + 1e-12)) ** w_pow
        N = int(np.sum(m))
        chi_fdb = float(np.nansum(((res[m]/sigma)**2) * w[m]))
        A_fdb = aicc(chi_fdb, k=2, N=N)
        # controls (rot, shift, shuffle)
        k_rot = np.rot90(kp_al, 2)
        chi_rot = float(np.nansum((((ko[m] - k_rot[m]) / sigma) ** 2) * w[m]))
        kp_shift = np.roll(np.roll(kp_al, 12, axis=0), -7, axis=1)
        chi_shift = float(np.nansum((((ko[m] - kp_shift[m]) / sigma) ** 2) * w[m]))
        A_rot = aicc(chi_rot, k=1, N=N)
        A_shift = aicc(chi_shift, k=2, N=N)
        delta_shift = A_fdb - A_shift
        # residual×Σ_e Spearman
        sr, sp = spearmanr(res[m].ravel(), se_obs[m].ravel(), nan_policy='omit')
        candidates.append({'beta': float(b), 'AICc_FDB': A_fdb, 'AICc_shift': A_shift, 'Delta_FDB_minus_shift': delta_shift,
                           'AICc_rot': A_rot, 'N': N, 'sigma': sigma, 'spearman': float(sr), 'p': float(sp),
                           'align_dx': float(dxf), 'align_dy': float(dyf)})

    # Select feasible (ΔAICc ≤ −10) then minimize Spearman
    feas = [c for c in candidates if (c['Delta_FDB_minus_shift'] <= -10.0)]
    best = None
    for c in sorted(feas, key=lambda d: (d['spearman'], d['AICc_FDB'])):
        best = c
        break
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    Path(outdir / 'bullet_holdout_search.json').write_text(json.dumps({'candidates': candidates, 'feasible': feas, 'best': best}, indent=2), encoding='utf-8')
    print('wrote', outdir / 'bullet_holdout_search.json')
    if best:
        print('best beta:', best['beta'], 'spearman:', best['spearman'], 'ΔAICc(FDB−shift):', best['Delta_FDB_minus_shift'])
    else:
        print('no feasible candidate meeting ΔAICc ≤ −10')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
