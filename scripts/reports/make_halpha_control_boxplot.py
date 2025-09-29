#!/usr/bin/env python3
from __future__ import annotations
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

from scripts.fit_sparc_fdbl import read_sparc_massmodels
from src.models.fdbl import irradiance_log_bias, circular_profile


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


def aicc(chi2: float, k: int, N: int) -> float:
    if N - k - 1 <= 0:
        return float('nan')
    return float(chi2 + 2 * k + (2 * k * (k + 1)) / (N - k - 1))


def load_em(name: str) -> np.ndarray | None:
    from astropy.io import fits
    for cand in ['EM_pc_cm6.fits', 'Halpha_SB.fits']:
        p = Path('data/halpha') / name / cand
        if p.exists():
            try:
                return fits.getdata(p).astype(float)
            except Exception:
                return None
    return None


def normalize_em(img: np.ndarray) -> np.ndarray:
    v = np.asarray(img, dtype=float)
    m = np.isfinite(v)
    if not m.any():
        return v
    lo = float(np.nanpercentile(v[m], 5))
    hi = float(np.nanpercentile(v[m], 99.5))
    vv = np.zeros_like(v)
    vv[m] = v[m]
    vv = np.log10(np.clip(vv, a_min=max(lo, 1e-12), a_max=max(hi, 1e-12)))
    return vv


def field_from_em(em: np.ndarray, pix_kpc: float, eps_kpc: float) -> np.ndarray:
    gx, gy = irradiance_log_bias(em, pix_kpc=pix_kpc, strength=1.0, eps_kpc=eps_kpc, pad_factor=1)
    rgrid, gr = circular_profile(gx, gy, pix_kpc, nbins=64)
    left_val = float(gr[0]) if np.isfinite(gr[0]) else 0.0
    right_val = float(gr[-1]) if np.isfinite(gr[-1]) else left_val
    return rgrid, gr, left_val, right_val


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description='Hα/EM controls: rotate/shift with ΔAICc stats')
    ap.add_argument('--n-rotate', type=int, default=50, help='random rotation replicates per galaxy')
    ap.add_argument('--n-shift', type=int, default=50, help='random circular-shift replicates per galaxy')
    ap.add_argument('--max-angle', type=float, default=180.0, help='max absolute rotation angle [deg] for random rotations')
    args = ap.parse_args()
    names = [p.name for p in (Path('data/halpha').iterdir() if Path('data/halpha').exists() else []) if p.is_dir()]
    out_dir = Path('server/public/reports'); out_dir.mkdir(parents=True, exist_ok=True)
    png = out_dir / 'control_tests_box.png'
    html = out_dir / 'control_halpha_tests.html'
    summary_json = out_dir / 'control_halpha_tests_summary.json'

    deltas_rotate: list[float] = []
    deltas_shift: list[float] = []
    used = []

    rng = np.random.default_rng(20250911)
    for nm in names:
        em = load_em(nm)
        if em is None:
            continue
        try:
            rc = read_sparc_massmodels(Path('data/sparc/MassModels_Lelli2016c.mrt'), nm)
        except Exception:
            continue

        em0 = normalize_em(em)
        pix = 0.2; eps = 0.8
        # Observed accel and mass components
        R = rc.R; Vobs = rc.Vobs; eV0 = np.maximum(rc.eV, 1e-6)
        floor = np.clip(0.03 * np.abs(Vobs), 3.0, 7.0)
        eV = np.sqrt(eV0*eV0 + floor*floor)
        g_obs, eg = to_accel(R, Vobs, eV)
        Rm = np.maximum(R, 1e-6)
        g_gas = (1.33 * (rc.Vgas * rc.Vgas)) / Rm
        g_star0 = (rc.Vdisk * rc.Vdisk + rc.Vbul * rc.Vbul) / Rm

        # Original
        r0, gr0, lv0, rv0 = field_from_em(em0, pix, eps)
        g0 = np.interp(R, r0, gr0, left=lv0, right=rv0)
        mu0 = fit_mu_ls(g_obs, eg, g_star0, g0, g_gas)
        model0 = g_gas + mu0 * g_star0 + g0
        chi0 = chi2(g_obs, eg, model0); N = int(np.isfinite(model0).sum()); a0 = aicc(chi0, 1, N)

        # Random rotations
        try:
            from scipy import ndimage as ndi
        except Exception:
            ndi = None
        n_rot = int(max(args.n_rotate, 0))
        for _ in range(n_rot):
            if ndi is None:
                em_rot = np.rot90(em0, k=int(rng.integers(1, 4)))
            else:
                ang = float(rng.uniform(-abs(args.max_angle), abs(args.max_angle)))
                em_rot = ndi.rotate(em0, angle=ang, reshape=False, order=1, mode='nearest')
            r1, gr1, lv1, rv1 = field_from_em(em_rot, pix, eps)
            g1 = np.interp(R, r1, gr1, left=lv1, right=rv1)
            mu1 = fit_mu_ls(g_obs, eg, g_star0, g1, g_gas)
            model1 = g_gas + mu1 * g_star0 + g1
            a1 = aicc(chi2(g_obs, eg, model1), 1, N)
            deltas_rotate.append(a1 - a0)

        # Random circular shifts
        n_sh = int(max(args.n_shift, 0))
        H, W = em0.shape
        for _ in range(n_sh):
            sy = int(rng.integers(-H//4, H//4+1))
            sx = int(rng.integers(-W//4, W//4+1))
            em_shf = np.roll(np.roll(em0, sy, axis=0), sx, axis=1)
            r2, gr2, lv2, rv2 = field_from_em(em_shf, pix, eps)
            g2 = np.interp(R, r2, gr2, left=lv2, right=rv2)
            mu2 = fit_mu_ls(g_obs, eg, g_star0, g2, g_gas)
            model2 = g_gas + mu2 * g_star0 + g2
            a2 = aicc(chi2(g_obs, eg, model2), 1, N)
            deltas_shift.append(a2 - a0)

        used.append(nm)

    # Save PNG boxplot
    if used:
        fig, ax = plt.subplots(1, 1, figsize=(5.6, 3.6))
        data = [np.array(deltas_rotate), np.array(deltas_shift)]
        ax.boxplot(data, labels=['回転対照', '平行移動対照'], showfliers=False)
        ax.axhline(0.0, color='#999', lw=1.0)
        ax.set_ylabel('ΔAICc = AICc(control) − AICc(original)')
        ax.set_title('Hα/EM 対照検証（ΔAICc 箱ひげ）')
        fig.tight_layout(); fig.savefig(png, dpi=140); plt.close(fig)
    else:
        png.write_text('', encoding='utf-8')

    # Effect size d（平均/標準偏差で簡易）
    def eff_d(arr: list[float]) -> float | None:
        a = np.array(arr, dtype=float)
        a = a[np.isfinite(a)]
        if a.size < 2:
            return None
        return float(np.nanmean(a) / (np.nanstd(a, ddof=1) + 1e-12))

    out = {
        'used': used,
        'rotate': {
            'n': int(np.isfinite(deltas_rotate).sum()),
            'median': float(np.nanmedian(deltas_rotate)) if deltas_rotate else None,
            'iqr': (float(np.nanpercentile(deltas_rotate, 75)) - float(np.nanpercentile(deltas_rotate, 25))) if deltas_rotate else None,
            'win_rate': float(np.mean([1.0 if (d is not None and d > 0) else 0.0 for d in deltas_rotate])) if deltas_rotate else None,
            'cohen_d': eff_d(deltas_rotate),
        },
        'shift': {
            'n': int(np.isfinite(deltas_shift).sum()),
            'median': float(np.nanmedian(deltas_shift)) if deltas_shift else None,
            'iqr': (float(np.nanpercentile(deltas_shift, 75)) - float(np.nanpercentile(deltas_shift, 25))) if deltas_shift else None,
            'win_rate': float(np.mean([1.0 if (d is not None and d > 0) else 0.0 for d in deltas_shift])) if deltas_shift else None,
            'cohen_d': eff_d(deltas_shift),
        },
        'note': 'ΔAICc>0 が望ましい（対照で適合が悪化）。EMの空間スケールは既定pix=0.2kpcで近似。'
    }
    summary_json.write_text(json.dumps(out, indent=2), encoding='utf-8')
    # HTML wrapper
    body = [f"<div class=card><p>回転: n={out['rotate']['n']}, median={out['rotate']['median']}, IQR={out['rotate']['iqr']}, win={out['rotate']['win_rate']}, d={out['rotate']['cohen_d']}</p>",
            f"<p>平行移動: n={out['shift']['n']}, median={out['shift']['median']}, IQR={out['shift']['iqr']}, win={out['shift']['win_rate']}, d={out['shift']['cohen_d']}</p>"
            f"<p><small>{out['note']}</small></p></div>"]
    if used and png.exists():
        body.append(f'<div class=card><p><img src="{png.name}" style="max-width:100%"></p></div>')
    else:
        body.append('<div class=card><p><small>Hα/EM データが見つからないため集計できませんでした。</small></p></div>')
    html.write_text('<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                    '<title>対照検証（Hα/EM; ΔAICc）</title><link rel="stylesheet" href="../styles.css"></head><body>'
                    '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div>'
                    '<nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav>'
                    '</div></header><main class="wrap"><h1>対照検証（Hα/EM; ΔAICc）</h1>' + '\n'.join(body) + '</main></body></html>',
                    encoding='utf-8')
    print('wrote', summary_json, 'and', html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
