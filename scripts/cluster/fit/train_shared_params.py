#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import asdict
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


def parse_grid(env_key: str, default_vals: list[float]) -> list[float]:
    s = os.environ.get(env_key, '')
    if not s:
        return default_vals
    out = []
    for tok in s.split(','):
        tok = tok.strip()
        if not tok:
            continue
        try:
            out.append(float(tok))
        except Exception:
            pass
    return out or default_vals


def main() -> int:
    # Training clusters and output
    train_names = os.environ.get('TRAIN_CLUSTERS', 'Abell1689,CL0024').split(',')
    train_roots = [Path(f'data/cluster/{n.strip()}') for n in train_names if n.strip()]
    out_json = Path('data/cluster/params_cluster.json')
    out_json.parent.mkdir(parents=True, exist_ok=True)

    # Fixed per sprint brief
    alphas = parse_grid('GRID_ALPHA', [0.6])
    Cs     = parse_grid('GRID_C',     [0.05])
    betas  = parse_grid('GRID_BETA',  [0.3, 0.5, 0.7, 0.9])
    xis    = parse_grid('GRID_XI',    [0.05, 0.2, 0.4, 0.7])
    ps     = parse_grid('GRID_P',     [0.5, 0.7, 1.0])
    tauqs  = parse_grid('GRID_TAUQ',  [0.45, 0.6, 0.7])
    dtfrac = float(os.environ.get('GRID_DELTA_TAU_FRAC', '0.1'))
    s_gates = parse_grid('GRID_S_GATE', [1.0])
    se_transform = os.environ.get('SE_TRANSFORM', 'none')
    W_CORR_FRAC = float(os.environ.get('W_CORR_FRAC', '0.0'))
    xi_sats = parse_grid('GRID_XI_SAT', [1e12])
    q_knees = parse_grid('GRID_Q_KNEE', [-1.0])
    # Gate multi-scale sigmas (comma-separated float list), default 2,4,8
    def parse_list_float(s: str) -> list[float]:
        out = []
        for t in s.split(','):
            t=t.strip()
            if not t:
                continue
            try:
                out.append(float(t))
            except Exception:
                pass
        return out
    gate_sigmas = parse_list_float(os.environ.get('GATE_SIGMAS', '2,4,8'))

    # Load maps
    train = []
    for rt in train_roots:
        dm = load_maps(rt)
        if dm is None:
            print('skip (missing maps):', rt)
            continue
        train.append((rt.name, ) + dm)
    if not train:
        print('no training data found; abort')
        return 1

    best = None
    results = []
    # Progress/ETA setup
    n_alpha, n_C, n_beta, n_xi, n_p, n_tauq = len(alphas), len(Cs), len(betas), len(xis), len(ps), len(tauqs)
    n_sg, n_xisat, n_qk = len(s_gates), len(xi_sats), len(q_knees)
    total = n_alpha * n_C * n_beta * n_xi * n_p * n_tauq * n_sg * n_xisat * n_qk
    done = 0
    import time as _time
    t0 = _time.time()
    for a in alphas:
        for c in Cs:
            for b in betas:
                for xi in xis:
                    for p in ps:
                        for tq in tauqs:
                            for sg in s_gates:
                                for xs in xi_sats:
                                    for qk in q_knees:
                                        A_list = []
                                        Spear_list = []
                                        for _, oc, se, kobs, pix in train:
                                            kpred = predict_kappa(oc, se, pix, MinKernelParams(alpha=float(a), beta=float(b), C=float(c), xi=float(xi), p=float(p), tau_q=float(tq), delta_tau_frac=dtfrac, se_transform=se_transform, s_gate=float(sg), xi_sat=float(xs), q_knee=float(qk), gate_sigmas=tuple(gate_sigmas)))
                                            if kpred.shape != kobs.shape:
                                                zy, zx = kobs.shape[0]/kpred.shape[0], kobs.shape[1]/kpred.shape[1]
                                                kpred = ndi.zoom(kpred, zoom=(zy, zx), order=1)
                                            # PSF match lightly (σ=0.5 pix)
                                            ko = ndi.gaussian_filter(kobs, sigma=0.5)
                                            kp = ndi.gaussian_filter(kpred, sigma=0.5)
                                            # Subpixel align (k=2 for alignment)
                                            kp_al, dyf, dxf = align_fft(kp, ko)
                                            res = (ko - kp_al)
                                            med = float(np.nanmedian(res)); mad = float(np.nanmedian(np.abs(res - med)))
                                            sigma = max(1.4826*mad, 1e-6)
                                            m = np.isfinite(ko) & np.isfinite(kp_al)
                                            if not np.any(m):
                                                continue
                                            # weight w = (Σ_e/⟨Σ_e⟩)^1
                                            se_obs = se if se.shape == ko.shape else ndi.zoom(se, zoom=(ko.shape[0]/se.shape[0], ko.shape[1]/se.shape[1]), order=1)
                                            w = (se_obs / (np.nanmean(se_obs) + 1e-12)) ** 1.0
                                            wv = w[m]
                                            chi2 = float(np.nansum(((res[m]/sigma)**2) * wv))
                                            A = aicc(chi2, k=2, N=int(np.sum(m)))
                                            A_list.append(A)
                                            # Spearman residual×Σ_e (global)
                                            try:
                                                s, _ = spearmanr(res[m].ravel(), se_obs[m].ravel(), nan_policy='omit')
                                            except Exception:
                                                s = np.nan
                                            Spear_list.append(float(s))
                            if not A_list:
                                continue
                            A_mean = float(np.nanmean(A_list))
                            S_mean = float(np.nanmean(Spear_list))
                            # Mixed objective: AICc + λ·S_mean with λ = W_CORR_FRAC * A_mean (favor negative Spearman)
                            lam = W_CORR_FRAC * A_mean
                            score = A_mean + lam * S_mean
                            row = {'alpha':float(a),'beta':float(b),'C':float(c),'xi':float(xi),'p':float(p),'tau_q':float(tq),'delta_tau_frac':dtfrac,'s_gate':float(sg),'se_transform':se_transform,'xi_sat':float(xs),'q_knee':float(qk),'gate_sigmas':gate_sigmas,
                                    'mean_AICc':A_mean,'mean_Spearman':S_mean,'score':score,'lambda':lam}
                            results.append(row)
                            if (best is None) or (score < best.get('score', float('inf')) - 1e-6):
                                best = row
                            # progress
                            done += 1
                            if done == 1 or done % max(1, total//100) == 0:
                                dt = _time.time() - t0
                                eta = (dt/done) * (total - done) if done>0 else float('nan')
                                print(f"[train][{done}/{total}] AICc={A_mean:.2e}, Spear={S_mean:.3f}, score={score:.2e} | elapsed={dt/60:.1f}m, ETA={eta/60:.1f}m", flush=True)

    if best is None:
        print('no viable parameter set')
        return 2

    # Save
    params = {k: best[k] for k in ['alpha','beta','C','xi','p','tau_q','delta_tau_frac','s_gate','se_transform','xi_sat','q_knee','gate_sigmas']}
    sha = __import__('hashlib').sha256(json.dumps(params, sort_keys=True).encode('utf-8')).hexdigest()
    out = {**params, 'sha256': sha, 'train_clusters': [n for (n, *_rest) in train]}
    out_json.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print('wrote', out_json)
    # Also drop a small summary to reports
    Path('server/public/reports').mkdir(parents=True, exist_ok=True)
    Path('server/public/reports/train_shared_params_summary.json').write_text(json.dumps({'best': best, 'grid_sizes': {'alpha':len(alphas),'beta':len(betas),'C':len(Cs),'xi':len(xis),'p':len(ps),'tau_q':len(tauqs)}}, indent=2), encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
