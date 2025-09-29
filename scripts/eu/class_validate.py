#!/usr/bin/env python3
from __future__ import annotations

"""
CLASS 連携（プロト）: baseline P(k,z) を取得し、Late‑FDB の μ(a,k) による
スケール依存成長 D_k(a) を用いた近似補正 P'(k,z) ≈ P_LCDM(k,z) × [D_k/D_0]^2 を評価。

注意: 現段階では CLASS の MG 拡張を直接は使わず、growth ODE に μ(a,k) を挿入して
成長のみを補正する近似。厳密検証（再計算された転移関数や再結合物理への影響）は
将来的に hi_class/MGCAMB で行う。
"""

import json
import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline

from src.cosmo.growth_solver import growth_factor, Cosmology
from src.cosmo.mu_late import mu_late

try:
    from analysis.bao_likelihood import evaluate_bao_likelihood
except ImportError:  # pragma: no cover - optional dependency in minimal installs
    evaluate_bao_likelihood = None  # type: ignore

try:
    from analysis.rsd_likelihood import evaluate_rsd_from_growth
except ImportError:  # pragma: no cover
    evaluate_rsd_from_growth = None  # type: ignore


try:
    from analysis.solar_penalty import compute_solar_penalty
except ImportError:  # pragma: no cover
    compute_solar_penalty = None  # type: ignore


def _smooth_no_wiggle(k: np.ndarray, pk: np.ndarray, s_factor: float = 0.003) -> np.ndarray:
    # 対数軸でスプライン平滑（wiggle-less近似）
    x = np.log(k)
    y = np.log(pk)
    s = s_factor * len(k)
    spl = UnivariateSpline(x, y, s=s)
    yw = spl(x)
    return np.exp(yw)


def class_baseline(Om0=0.315, Ob0=0.049, h=0.674, ns=0.965, As=2.1e-9,
                   z_list=(0.35, 0.57, 1.0)):
    try:
        from classy import Class  # type: ignore
        try:
            from classy import __version__ as classy_version  # type: ignore[attr-defined]
        except Exception:
            try:
                import importlib.metadata as importlib_metadata
                classy_version = importlib_metadata.version('classy')
            except Exception:
                classy_version = ''
    except Exception:
        return None
    cosmo = Class()
    params = {
        'output': 'mPk',
        'P_k_max_1/Mpc': 2.0,
        'z_max_pk': max(z_list) + 0.1,
        'Omega_b': Ob0,
        'Omega_cdm': Om0 - Ob0,
        'h': h,
        'A_s': As,
        'n_s': ns,
        'tau_reio': 0.0544,
    }
    cosmo.set(params)
    cosmo.compute()
    # 共通 k グリッド
    k = np.logspace(-3, 0.3, 400)  # 1/Mpc
    out = {'k': k.tolist(), 'z': list(z_list), 'pk': []}
    for z in z_list:
        pk = np.array([cosmo.pk(kk, z) for kk in k])
        out['pk'].append(pk.tolist())
    cosmo.struct_cleanup(); cosmo.empty()
    out['params'] = params
    out['class_version'] = locals().get('classy_version', '')
    return out


def apply_mu_growth(pk_baseline: dict, cfg: dict) -> dict:
    cos = Cosmology()
    k = np.array(pk_baseline['k'])
    zs = pk_baseline['z']
    pks = [np.array(x) for x in pk_baseline['pk']]
    out_pks = []
    for z, pk in zip(zs, pks):
        a = 1.0 / (1.0 + z)
        # baseline growth D0(a)
        a_grid = np.geomspace(max(a/200.0, 1e-4), a, 256)
        D0 = growth_factor(a_grid, k=1.0, cosmo=cos, use_mu_late=False)
        D0a = float(D0[-1])
        # scale-dependent Dk(a) with mu_late(a,k)
        Dk = np.array([
            growth_factor(
                a_grid,
                kk,
                cosmo=cos,
                use_mu_late=True,
                eps_max=float(cfg['eps_max']),
                a_on=float(cfg['a_on']),
                da=float(cfg['da']),
                k_c=float(cfg['k_c']),
                k_sup=cfg.get('k_sup'),
                n_sup=float(cfg.get('n_sup', 2.0)),
            )[-1]
            for kk in k
        ])
        ratio2 = (Dk / max(D0a, 1e-12)) ** 2
        out_pks.append((pk * ratio2).tolist())
    return {'k': pk_baseline['k'], 'z': zs, 'pk_prime': out_pks}


def summarize_bao(k: np.ndarray, pk0: np.ndarray, pk1: np.ndarray) -> dict:
    # BAO 帯（0.02..0.3 1/Mpc）での振幅とピークの簡易差分
    m = (k >= 0.02) & (k <= 0.3)
    def wiggle(pk):
        nw = _smooth_no_wiggle(k[m], pk[m])
        return pk[m] / np.maximum(nw, 1e-30)
    w0 = wiggle(pk0)
    w1 = wiggle(pk1)
    amp0 = float(np.std(w0))
    amp1 = float(np.std(w1))
    # 最初のピーク近傍（~0.1 1/Mpc）
    ksub = k[m]
    w1s = w1
    idx = np.argmin(np.abs(ksub - 0.1))
    # 近傍で最大となる点
    i0 = max(0, idx - 10); i1 = min(len(ksub), idx + 11)
    pkpos0 = float(ksub[i0 + int(np.argmax(w0[i0:i1]))])
    pkpos1 = float(ksub[i0 + int(np.argmax(w1s[i0:i1]))])
    return {
        'amp_ratio': float(amp1 / max(amp0, 1e-12)),
        'peak_shift': float(pkpos1 - pkpos0),
        'k_peak0': pkpos0,
        'k_peak1': pkpos1,
    }


def main() -> int:
    cfg_p = Path('cfg/early_fdb.json')
    cfg = json.loads(cfg_p.read_text(encoding='utf-8')) if cfg_p.exists() else {
        'eps_max': 0.1, 'a_on': 1/21, 'da': 0.02, 'k_c': 0.2
    }
    meta = {'available': False}
    base = class_baseline()
    outdir = Path('assets/figures/early_universe'); outdir.mkdir(parents=True, exist_ok=True)
    fig_path = outdir / 'Fig-EU1c_class_bao.png'
    if base is None:
        # Placeholder
        plt.figure(figsize=(6,3))
        plt.text(0.5, 0.6, 'CLASS が見つかりません\n(proxy のみ)', ha='center', va='center')
        plt.axis('off'); plt.tight_layout(); plt.savefig(fig_path, dpi=160); plt.close()
        Path('server/public/state_of_the_art').mkdir(parents=True, exist_ok=True)
        Path('server/public/state_of_the_art/early_universe_class.json').write_text(
            json.dumps({'available': False}, indent=2, ensure_ascii=False), encoding='utf-8')
        print('CLASS not available; wrote placeholder:', fig_path)
        return 0
    # Apply growth-based correction
    pkp = apply_mu_growth(base, cfg)
    k = np.array(base['k']); zlist = base['z']
    # Choose z=0.57 for plot
    zi = int(np.argmin(np.abs(np.array(zlist) - 0.57)))
    pk0 = np.array(base['pk'][zi])
    pk1 = np.array(pkp['pk_prime'][zi])
    summ = summarize_bao(k, pk0, pk1)
    # Plot
    plt.figure(figsize=(7,4))
    plt.loglog(k, pk0, label='LCDM (CLASS)')
    plt.loglog(k, pk1, label='Late‑FDB (growth‑corrected)')
    plt.xlim(0.01, 0.5); plt.ylim(1e2, 1e5)
    plt.xlabel('k [1/Mpc]'); plt.ylabel('P(k) [(Mpc)^3]')
    plt.title(f'Fig‑EU1c: BAO 検証 (z≈{zlist[zi]:.2f})\nAmp×≈{summ["amp_ratio"]:.3f}, Δk≈{summ["peak_shift"]:.4f} 1/Mpc')
    plt.legend(); plt.tight_layout(); plt.savefig(fig_path, dpi=160); plt.close()

    public_root = Path('server/public/state_of_the_art')
    (public_root / 'figs').mkdir(parents=True, exist_ok=True)
    (public_root / 'data').mkdir(parents=True, exist_ok=True)
    fig_public = public_root / 'figs' / 'fig_eu1c.png'
    shutil.copyfile(fig_path, fig_public)

    class_params = base.get('params', {})
    class_version = base.get('class_version', '')
    # export CLASS params to ini-like file for hashing
    ini_lines = ['# Generated by scripts/eu/class_validate.py']
    for key in sorted(class_params):
        ini_lines.append(f"{key} = {class_params[key]}")
    ini_path = public_root / 'data' / 'fig_eu1c_class.ini'
    ini_path.write_text("\n".join(ini_lines) + "\n", encoding='utf-8')
    ini_sha = hashlib.sha256(ini_path.read_bytes()).hexdigest()

    shared_params_sha = ''
    sp_path = Path('data/shared_params.json')
    if sp_path.exists():
        shared_params_sha = hashlib.sha256(sp_path.read_bytes()).hexdigest()

    cfg_sha = hashlib.sha256(json.dumps(cfg, sort_keys=True).encode('utf-8')).hexdigest()
    data_payload = {
        'k': base['k'],
        'z': zlist,
        'pk_lcdm': base['pk'][zi],
        'pk_fdb': pkp['pk_prime'][zi],
        'summary': summ,
        'cfg': cfg,
        'class_params': class_params,
        'log': {
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'command': 'PYTHONPATH=. python scripts/eu/class_validate.py',
            'class_version': class_version,
            'shared_params_sha': shared_params_sha,
            'cfg_sha': cfg_sha,
            'class_ini_sha': ini_sha,
            'rng': None,
        },
    }

    bao_summary = None
    if evaluate_bao_likelihood is not None and class_params:
        try:
            bao_payload = evaluate_bao_likelihood(class_params)
        except FileNotFoundError as err:
            print(f'BAO likelihood skipped: {err}')
            bao_payload = None
        except RuntimeError as err:
            print(f'BAO likelihood skipped: {err}')
            bao_payload = None
        if bao_payload:
            data_payload['bao_likelihood'] = bao_payload
            bao_summary = {
                'chi2_total': bao_payload['chi2_total'],
                'ndof_total': bao_payload['ndof_total'],
                'p_value_total': bao_payload['p_value_total'],
                'bao_file': bao_payload.get('bao_file'),
            }
    rsd_summary = None
    rsd_payload_combined = None
    if evaluate_rsd_from_growth is not None:
        try:
            rsd_payload_fdb = evaluate_rsd_from_growth(use_mu_late=True)
            rsd_payload_lcdm = evaluate_rsd_from_growth(use_mu_late=False)
        except (FileNotFoundError, ValueError) as err:
            print(f'RSD likelihood skipped: {err}')
            rsd_payload_fdb = rsd_payload_lcdm = None
        if rsd_payload_fdb and rsd_payload_lcdm:
            rsd_payload_combined = {
                'late_fdb': rsd_payload_fdb,
                'lcdm': rsd_payload_lcdm,
            }
            data_payload['rsd_likelihood'] = rsd_payload_combined
            chi2_fdb = rsd_payload_fdb.get('chi2_total')
            chi2_lcdm = rsd_payload_lcdm.get('chi2_total')
            ndof = rsd_payload_fdb.get('ndof_total')
            delta = None
            if isinstance(chi2_fdb, (int, float)) and isinstance(chi2_lcdm, (int, float)):
                delta = chi2_fdb - chi2_lcdm
            rsd_summary = {
                'chi2_late_fdb': chi2_fdb,
                'chi2_lcdm': chi2_lcdm,
                'ndof_total': rsd_payload_fdb.get('ndof_total'),
                'delta_chi2': delta,
            }
    solar_summary = None
    if compute_solar_penalty is not None:
        try:
            solar_result = compute_solar_penalty(cfg)
        except Exception as err:
            print(f'Solar penalty skipped: {err}')
            solar_result = None
        if solar_result is not None:
            solar_summary = solar_result.to_dict()
            data_payload['solar_penalty'] = solar_summary
    data_path = public_root / 'data' / 'fig_eu1c.json'
    data_path.write_text(json.dumps(data_payload, indent=2, ensure_ascii=False), encoding='utf-8')

    if rsd_payload_combined is not None:
        rsd_out = public_root / 'data' / 'rsd_likelihood.json'
        rsd_out.write_text(json.dumps(rsd_payload_combined, indent=2, ensure_ascii=False), encoding='utf-8')

    meta = {
        'available': True,
        'z': zlist[zi],
        'amp_ratio': summ['amp_ratio'],
        'peak_shift': summ['peak_shift'],
        'class_version': class_version,
        'shared_params_sha': shared_params_sha,
        'cfg_sha': cfg_sha,
        'class_ini_sha': ini_sha,
    }
    if bao_summary is not None:
        meta['bao'] = bao_summary
    if rsd_summary is not None:
        meta['rsd'] = rsd_summary
    if solar_summary is not None:
        meta['solar'] = solar_summary
    public_root.mkdir(parents=True, exist_ok=True)
    (public_root / 'early_universe_class.json').write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
    print('wrote CLASS validation:', fig_path, meta)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
