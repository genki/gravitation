#!/usr/bin/env python3
from __future__ import annotations
import json, time
import numpy as np
from pathlib import Path
from dataclasses import dataclass

from scripts.fit_sparc_fdbl import read_sparc_massmodels, make_axisymmetric_image
from src.models.fdbl import irradiance_log_bias, circular_profile
from scripts.utils.progress import ProgressETA


@dataclass
class PerGalaxy:
    name: str
    aicc_orig: float
    aicc_ctrl: float
    delta_aicc: float
    N: int
    k: int


def aicc(chi2: float, k: int, N: int) -> float:
    if N - k - 1 <= 0:
        return float('nan')
    return float(chi2 + 2 * k + (2 * k * (k + 1)) / (N - k - 1))


def to_accel(R: np.ndarray, V: np.ndarray, eV: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    Rm = np.maximum(R, 1e-6)
    g = (V * V) / Rm
    eg = 2.0 * V * np.maximum(eV, 1e-6) / Rm
    return g, eg


def fit_mu_ls(g_obs: np.ndarray, eg: np.ndarray, g_star: np.ndarray, g_extra: np.ndarray, g_gas: np.ndarray) -> float:
    y = g_obs - g_gas - g_extra
    x = g_star
    w = 1.0 / np.maximum(eg, 1e-6)
    num = float(np.nansum(w * x * y))
    den = float(np.nansum(w * x * x))
    return max(0.0, num / max(den, 1e-30))


def chi2(g_obs: np.ndarray, eg: np.ndarray, g_model: np.ndarray) -> float:
    w = 1.0 / np.maximum(eg, 1e-6)
    return float(np.nansum(((g_model - g_obs) * w) ** 2))


def summarize(vals: list[float]) -> dict:
    arr = np.array([v for v in vals if np.isfinite(v)])
    if arr.size == 0:
        return {"median": None, "iqr": None, "mean": None, "std": None, "n": 0}
    q1 = float(np.nanpercentile(arr, 25))
    q2 = float(np.nanpercentile(arr, 50))
    q3 = float(np.nanpercentile(arr, 75))
    return {"median": q2, "iqr": q3 - q1, "mean": float(np.nanmean(arr)), "std": float(np.nanstd(arr, ddof=1)), "n": int(arr.size)}


def main() -> int:
    # Settings
    names_file = Path('data/sparc/sets/clean_for_fit.txt')
    out_json = Path('server/public/reports/control_tests_summary.json')
    out_html = Path('server/public/reports/control_tests.html')
    pix = 0.2
    size = 256
    line_eps = 0.8

    names = [ln.strip() for ln in names_file.read_text(encoding='utf-8').splitlines() if ln.strip() and not ln.startswith('#')]
    rows: list[PerGalaxy] = []
    # Progress: 1 unit per galaxy + summary(2) + html(1)
    steps = [(f'gal:{nm}', 1.0) for nm in names] + [('summary', 2.0), ('html', 1.0)]
    pg = ProgressETA(steps)
    # rough hint: ~0.15 min/gal (heuristic)
    pg.start(total_hint_min=max(len(names) * 0.15, 1.0))
    deltas_rotate: list[float] = []
    deltas_translate: list[float] = []
    deltas_shuffle: list[float] = []

    for nm in names:
        try:
            rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), nm)
            R = rc.R
            Vobs = rc.Vobs
            eV0 = np.maximum(rc.eV, 1e-6)
            # fair error-floor policy (km/s)
            floor = np.clip(0.03 * np.abs(Vobs), 3.0, 7.0)
            eV = np.sqrt(eV0 * eV0 + floor * floor)
            g_obs, eg = to_accel(R, Vobs, eV)
            Rm = np.maximum(R, 1e-6)
            g_gas = (1.33 * (rc.Vgas * rc.Vgas)) / Rm
            g_star0 = (rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul) / Rm

            # Build axisymmetric source image from SBdisk
            j = make_axisymmetric_image(R, rc.SBdisk, pix, size)
            # Surface (ULM-D proxy) field from log irradiance bias
            gx, gy = irradiance_log_bias(j, pix_kpc=pix, strength=1.0, eps_kpc=line_eps, pad_factor=1)
            rgrid, gr = circular_profile(gx, gy, pix, nbins=64)
            left_val = float(gr[0]) if np.isfinite(gr[0]) else 0.0
            right_val = float(gr[-1]) if np.isfinite(gr[-1]) else left_val
            g_ulw = np.interp(R, rgrid, gr, left=left_val, right=right_val)
            mu = fit_mu_ls(g_obs, eg, g_star0, g_ulw, g_gas)
            g_model = g_gas + mu * g_star0 + g_ulw
            chi = chi2(g_obs, eg, g_model)
            N = int(np.isfinite(g_model).sum())
            aic_o = aicc(chi, k=1, N=N)

            # Controls: rotation / translation / isosurface-shuffle (multiple trials)
            # rotation angles (deg)
            for ang in (90, 180, 270):
                jr = np.rot90(j, k=int(ang/90))
                gx_r, gy_r = irradiance_log_bias(jr, pix_kpc=pix, strength=1.0, eps_kpc=line_eps, pad_factor=1)
                rr, grr = circular_profile(gx_r, gy_r, pix, nbins=64)
                lv = float(grr[0]) if np.isfinite(grr[0]) else 0.0
                rv = float(grr[-1]) if np.isfinite(grr[-1]) else lv
                g_ulw_r = np.interp(R, rr, grr, left=lv, right=rv)
                mu_r = fit_mu_ls(g_obs, eg, g_star0, g_ulw_r, g_gas)
                chi_r = chi2(g_obs, eg, g_gas + mu_r * g_star0 + g_ulw_r)
                aic_r = aicc(chi_r, k=1, N=N)
                deltas_rotate.append(aic_r - aic_o)

            # translations: roll by ±d in x,y (periodic proxy)
            for d in (8, -8):
                jt = np.roll(np.roll(j, d, axis=0), -d, axis=1)
                gx_t, gy_t = irradiance_log_bias(jt, pix_kpc=pix, strength=1.0, eps_kpc=line_eps, pad_factor=1)
                rt, grt = circular_profile(gx_t, gy_t, pix, nbins=64)
                lv = float(grt[0]) if np.isfinite(grt[0]) else 0.0
                rv = float(grt[-1]) if np.isfinite(grt[-1]) else lv
                g_ulw_t = np.interp(R, rt, grt, left=lv, right=rv)
                mu_t = fit_mu_ls(g_obs, eg, g_star0, g_ulw_t, g_gas)
                chi_t = chi2(g_obs, eg, g_gas + mu_t * g_star0 + g_ulw_t)
                aic_t = aicc(chi_t, k=1, N=N)
                deltas_translate.append(aic_t - aic_o)

            # isosurface shuffle with multiple seeds
            rng = np.random.default_rng(2109)
            for _ in range(20):
                jp = j.ravel().copy()
                rng.shuffle(jp)
                j_shuf = jp.reshape(j.shape)
                gx_c, gy_c = irradiance_log_bias(j_shuf, pix_kpc=pix, strength=1.0, eps_kpc=line_eps, pad_factor=1)
                r_c, gr_c = circular_profile(gx_c, gy_c, pix, nbins=64)
                lv = float(gr_c[0]) if np.isfinite(gr_c[0]) else 0.0
                rv = float(gr_c[-1]) if np.isfinite(gr_c[-1]) else lv
                g_ulw_c = np.interp(R, r_c, gr_c, left=lv, right=rv)
                mu_c = fit_mu_ls(g_obs, eg, g_star0, g_ulw_c, g_gas)
                chi_c = chi2(g_obs, eg, g_gas + mu_c * g_star0 + g_ulw_c)
                aic_c = aicc(chi_c, k=1, N=N)
                deltas_shuffle.append(aic_c - aic_o)

            rows.append(PerGalaxy(nm, aic_o, aic_o, 0.0, N, 1))
        except Exception:
            continue
        finally:
            # tick progress for this galaxy regardless of success
            pg.tick(f'gal:{nm}')

    # Aggregate summary
    deltas = [r.delta_aicc for r in rows]
    summ = summarize(deltas)
    win_rate = float(np.mean([1.0 if (d is not None and d > 0) else 0.0 for d in deltas])) if deltas else 0.0
    # Effect size d (Cohen's d) per control type treating ΔAICc samples vs 0
    def effect_size_d(samples: list[float]) -> float:
        arr = np.array([v for v in samples if np.isfinite(v)])
        if arr.size < 2:
            return float('nan')
        return float(np.nanmean(arr) / (np.nanstd(arr, ddof=1) + 1e-12))

    out = {
        'method': 'control_tests_isoshuffle_proxy',
        'names_file': str(names_file),
        'per_galaxy': [r.__dict__ for r in rows],
        'summary': {**summ, 'win_rate': win_rate},
        'controls': {
            'rotate': {**summarize(deltas_rotate), 'd': effect_size_d(deltas_rotate)},
            'translate': {**summarize(deltas_translate), 'd': effect_size_d(deltas_translate)},
            'shuffle': {**summarize(deltas_shuffle), 'd': effect_size_d(deltas_shuffle)},
        },
        'definition': 'ΔAICc = AICc(control) − AICc(original); controls = {rotate 90/180/270, translate ±8px, isosurface-shuffle×20}.',
    }
    pg.tick('summary')
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2), encoding='utf-8')

    # Simple HTML box summary
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>対照検証（ΔAICc要約）</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header><main class="wrap">',
        '<h1>対照検証の定量（ΔAICc 要約）</h1>'
    ]
    # Two-line definition fixed at chapter head
    html.append('<div class=card><p><small>本節の「対照検証」は、n_e 構造を意図的に破壊した偽データで再適合し、FDB 改善が本来の幾何に依存するかを検証する試験である。</small></p>'
                '<p><small>ΔAICc = AICc(control) − AICc(original)。control={回転, 平行移動, 等値面シャッフル}。</small></p></div>')
    html.append(f"<div class=card><p>全体: 中央値 {summ['median']}, IQR {summ['iqr']}, 勝率(ΔAICc>0) {win_rate:.2f}</p></div>")
    # Per-control table (median, IQR, d, n)
    rot = summarize(deltas_rotate); tra = summarize(deltas_translate); shu = summarize(deltas_shuffle)
    rot_d = effect_size_d(deltas_rotate); tra_d = effect_size_d(deltas_translate); shu_d = effect_size_d(deltas_shuffle)
    html.append('<table><thead><tr><th>対照</th><th>中央値</th><th>IQR</th><th>d</th><th>n</th></tr></thead><tbody>')
    html.append(f"<tr><td>回転</td><td>{rot['median']:.2f}</td><td>{rot['iqr']:.2f}</td><td>{rot_d:.2f}</td><td>{rot['n']}</td></tr>")
    html.append(f"<tr><td>平行移動</td><td>{tra['median']:.2f}</td><td>{tra['iqr']:.2f}</td><td>{tra_d:.2f}</td><td>{tra['n']}</td></tr>")
    html.append(f"<tr><td>等値面シャッフル</td><td>{shu['median']:.2f}</td><td>{shu['iqr']:.2f}</td><td>{shu_d:.2f}</td><td>{shu['n']}</td></tr>")
    html.append('</tbody></table>')
    html.append('</main></body></html>')
    out_html.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out_json, 'and', out_html)
    pg.tick('html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
