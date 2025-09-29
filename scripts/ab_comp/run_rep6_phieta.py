#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from scripts.fit_sparc_fdbl import read_sparc_massmodels
from scripts.compare_fit_multi import chi2
from src.fdb.a_from_info import info_bias_profile_from_map
from theory.info_decoherence import EtaParams
from astropy.io import fits


def with_error_floor(R: np.ndarray, Vobs: np.ndarray, eV: np.ndarray,
                     frac: float, vmin: float, vmax: float) -> Tuple[np.ndarray, np.ndarray]:
    Vobs = np.asarray(Vobs, float); eV = np.asarray(eV, float)
    floor = np.clip(frac * np.abs(Vobs), vmin, vmax)
    eVe = np.sqrt(np.maximum(eV, 1e-6) ** 2 + floor ** 2)
    Rm = np.maximum(R, 1e-6)
    g_obs = (Vobs * Vobs) / Rm
    eg = 2.0 * Vobs * eVe / Rm
    return g_obs, eg


def load_proxy_map(name: str) -> Tuple[np.ndarray, float]:
    p = Path(f'data/halpha/{name}/Halpha_SB.fits')
    if p.exists():
        img = fits.getdata(p).astype(float)
        hdr = fits.getheader(p)
        pix = float(hdr.get('PIXSCALE', 0.305)) / 206265.0 * 1.0
        if not np.isfinite(pix) or pix <= 0:
            pix = 0.2
        return img, pix
    rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), name)
    # axisymmetric fallback from SBdisk
    R = rc.R
    SB = rc.SBdisk
    size = 256
    y = (np.arange(size) - (size - 1) / 2.0) * 0.2
    x = (np.arange(size) - (size - 1) / 2.0) * 0.2
    yy, xx = np.meshgrid(y, x, indexing='ij'); rr = np.hypot(xx, yy)
    img = np.interp(rr.ravel(), R, SB, left=SB[0], right=SB[-1]).reshape(size, size)
    m = np.nanmax(img)
    if m > 0: img = img / m
    return img, 0.2


def aicc(chi2: float, k: int, N: int) -> float:
    return float(chi2 + 2*k + (2*k*(k+1))/max(N-k-1, 1))


def main() -> None:
    if os.environ.get('GRAV_BG_JOB') != '1':
        sys.stderr.write(
            "[guard] This heavy job must be launched via dispatcher.\n"
            "Use: make rep6-ab-fast-bg | rep6-ab-full-bg, or\n"
            "scripts/jobs/dispatch_bg.sh -n rep6_ab_fast -- 'PYTHONPATH=. ./.venv/bin/python scripts/ab_comp/run_rep6_phieta.py --fast'\n"
        )
        raise SystemExit(1)
    ap = argparse.ArgumentParser(description='rep6 — Phi·eta(情報流) representative table under fair settings')
    ap.add_argument('--fast', action='store_true')
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--downsample', type=int, default=2)
    ap.add_argument('--float32', action='store_true')
    ap.add_argument('--psf-sigma', nargs='+', type=float, default=[1.0, 1.5])
    ap.add_argument('--hipass', default='8-16')
    ap.add_argument('--errfloor', default='0.03,3,7')
    ap.add_argument('--k', type=int, default=2)
    ap.add_argument('--rng', type=int, default=42)
    ap.add_argument('--names-file', default='data/sparc/sets/rep6.txt')
    ap.add_argument('--out', default='data/results/rep6_phieta_fast.json')
    # Fair grid for Phi·eta
    ap.add_argument('--beta', nargs='+', type=float, default=[0.0, 0.3])
    ap.add_argument('--s', nargs='+', type=float, default=[0.4, 0.6, 1.0])
    ap.add_argument('--sigk', nargs='+', type=float, default=[0.5, 0.8, 1.2])
    ap.add_argument('--workers', type=int, default=0, help='parallel workers (0=auto when --workers-auto)')
    ap.add_argument('--workers-auto', action='store_true', help='use ~60% of available CPUs when workers=0')
    args = ap.parse_args()

    try:
        np.random.seed(int(args.rng))
    except Exception:
        pass

    if args.full:
        if 2.0 not in args.psf_sigma:
            args.psf_sigma = sorted(set(args.psf_sigma + [2.0]))
        args.downsample = 1
        args.float32 = False
        args.out = 'data/results/rep6_phieta_full.json'
        args.hipass = '4-8,8-16'

    names = [ln.strip() for ln in Path(args.names_file).read_text(encoding='utf-8').splitlines()
             if ln.strip() and not ln.startswith('#')]
    ef = [float(x) for x in args.errfloor.split(',')]
    ef_frac, ef_min, ef_max = float(ef[0]), float(ef[1]), float(ef[2])
    def _one(nm_s: Tuple[str, int]) -> Dict[str, Any]:
        nm, seed_off = nm_s
        try:
            try:
                np.random.seed(int(args.rng) + int(seed_off))
            except Exception:
                pass
            rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), nm)
            R = rc.R; Vobs = rc.Vobs; eV = np.maximum(rc.eV, 1e-6)
            g_obs, eg = with_error_floor(R, Vobs, eV, ef_frac, ef_min, ef_max)
            Rm = np.maximum(R, 1e-6)
            g_gas = (1.33 * (rc.Vgas*rc.Vgas)) / Rm
            g_star0 = (rc.Vdisk*rc.Vdisk + rc.Vbul*rc.Vbul) / Rm
            img, pix = load_proxy_map(nm)
            best = None
            for beta in args.beta:
                for s_kpc in args.s:
                    for sig in args.sigk:
                        k_grid = np.linspace(0.02, 1.0, 32)
                        phi_k = np.exp(-0.5 * (k_grid / float(sig))**2)
                        g_if = info_bias_profile_from_map(R, img, pix_kpc=pix, k_grid=k_grid, phi_k=phi_k,
                                                          eta_params=EtaParams(beta=float(beta), s_kpc=float(s_kpc)))
                        m = np.isfinite(g_obs) & np.isfinite(eg) & np.isfinite(g_gas) & np.isfinite(g_star0) & np.isfinite(g_if)
                        if not np.any(m):
                            continue
                        # weighted LS for mu, alpha
                        mb = m
                        w = 1.0 / np.maximum(eg[mb], 1e-6)
                        X1 = g_star0[mb]; X2 = g_if[mb]
                        Y  = g_obs[mb] - g_gas[mb]
                        S11 = float(np.nansum(w*X1*X1)); S22 = float(np.nansum(w*X2*X2)); S12 = float(np.nansum(w*X1*X2))
                        b1 = float(np.nansum(w*X1*Y)); b2 = float(np.nansum(w*X2*Y))
                        det = S11*S22 - S12*S12
                        if det <= 0:
                            continue
                        mu = (b1*S22 - b2*S12) / det
                        alpha = (S11*b2 - S12*b1) / det
                        gmod = g_gas + mu * g_star0 + alpha * g_if
                        chi = chi2(g_obs[mb], eg[mb], gmod[mb])
                        N = int(np.sum(mb))
                        aic = aicc(chi, k=args.k, N=N)
                        row = (aic, chi, mu, alpha, beta, s_kpc, sig, N)
                        if best is None or row[0] < best[0]:
                            best = row
            if best is None:
                return {'name': nm, 'error': 'Phi·eta failed'}
            aic, chi, mu, alpha, beta, s_kpc, sig, N = best
            return {
                'name': nm,
                'N': int(N),
                'k': int(args.k),
                'mu_if': float(mu),
                'alpha_if': float(alpha),
                'beta': float(beta),
                's_kpc': float(s_kpc),
                'sigk': float(sig),
                'chi2_if': float(chi),
                'AICc_if': float(aic),
            }
        except Exception:
            return {'name': nm, 'error': 'Phi·eta failed'}

    items = [(nm, i) for i, nm in enumerate(names)]
    workers = int(args.workers or 0)
    if workers <= 0 and args.workers_auto:
        try:
            import os as _os
            workers = max(1, int(0.6 * (_os.cpu_count() or 1)))
        except Exception:
            workers = 1
    workers = max(1, workers)
    if workers == 1:
        rows = [_one(it) for it in items]
    else:
        from multiprocessing import Pool
        import os as _os
        for var in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_MAX_THREADS']:
            _os.environ[var] = '1'
        with Pool(processes=workers) as pool:
            rows = list(pool.map(_one, items))

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    # reconstruct command for reproducibility footnote
    try:
        rel = Path(__file__).relative_to(Path(__file__).parents[2])
        cmd = 'PYTHONPATH=. python ' + str(rel) + ' ' + ' '.join([h for h in sys.argv[1:]])
    except Exception:
        cmd = 'python run_rep6_phieta.py ' + ' '.join([h for h in sys.argv[1:]])
    # meta and sha/git
    def _sha(path: str, algo: str = 'sha256', n: int = 12) -> str | None:
        p = Path(path)
        if not p.exists():
            return None
        import hashlib
        h = hashlib.sha256 if algo == 'sha256' else hashlib.sha1
        try:
            return h(p.read_bytes()).hexdigest()[:n]
        except Exception:
            return None
    try:
        git_sha = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=Path(__file__).parents[2]).decode().strip()
    except Exception:
        git_sha = ''
    meta = {
        'mode': 'FULL' if args.full else 'FAST',
        'psf_sigma': args.psf_sigma,
        'hipass': args.hipass,
        'errfloor': [ef_frac, ef_min, ef_max],
        'k': int(args.k),
        'rng': int(args.rng),
        'cmd': cmd,
        # use sha256(12) to align with other pages/footers
        'fair_json_sha': _sha('config/fair.json', 'sha256', 12),
        'shared_params_sha': _sha('data/shared_params.json', 'sha256', 12),
        'git_sha': git_sha,
    }
    payload = {'meta': meta, 'rows': rows}
    outp.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print('wrote', outp)


if __name__ == '__main__':
    main()
