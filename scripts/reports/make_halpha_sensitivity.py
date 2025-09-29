#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats, ndimage as ndi
from scripts.utils.mpl_fonts import use_jp_font


def em_to_ne_cm3(EM_pc_cm6: np.ndarray, L_pc: float) -> np.ndarray:
    L = max(float(L_pc), 1.0)
    return np.sqrt(np.maximum(EM_pc_cm6, 0.0) / L)


def plasma_freq_rad_s(ne_cm3: np.ndarray) -> np.ndarray:
    return 5.64e4 * np.sqrt(np.maximum(ne_cm3, 0.0))


def ring_median_residual(v: np.ndarray, nbins: int = 60) -> np.ndarray:
    ny, nx = v.shape
    yy, xx = np.indices((ny, nx))
    cy, cx = (ny - 1) / 2.0, (nx - 1) / 2.0
    r = np.hypot(xx - cx, yy - cy)
    edges = np.linspace(0, r.max(), nbins + 1)
    med = np.zeros_like(v) + np.nan
    for i in range(nbins):
        m = (r >= edges[i]) & (r < edges[i+1]) & np.isfinite(v)
        if m.any(): med[m] = np.nanmedian(v[m])
    return v - med


def corr_pair(EM: np.ndarray, V: np.ndarray, L_pc: float, scale: float) -> tuple[float, float]:
    # scale EM to emulate ON/OFF corrections (illustrative)
    EMs = np.clip(EM * float(scale), 0.0, None)
    # resolution guard
    if max(EMs.shape) > 1200:
        EMs = ndi.zoom(EMs, zoom=800.0/max(EMs.shape), order=1)
    ne = em_to_ne_cm3(EMs, L_pc)
    wcut = plasma_freq_rad_s(ne)
    Vres = ring_median_residual(V)
    if max(Vres.shape) > 1200:
        Vres = ndi.zoom(Vres, zoom=800.0/max(Vres.shape), order=1)
    # match grids
    zoom = (wcut.shape[0]/Vres.shape[0], wcut.shape[1]/Vres.shape[1])
    Vres = ndi.zoom(Vres, zoom=zoom, order=1)
    m = np.isfinite(wcut) & np.isfinite(Vres)
    if not np.any(m):
        return float('nan'), float('nan')
    x = np.log10(np.clip(wcut[m], 1e-8, None)); y = Vres[m]
    if np.std(x) == 0 or np.std(y) == 0 or np.sum(m) < 5:
        return float('nan'), float('nan')
    r, p = stats.pearsonr(x, y)
    return float(r), float(p)


def main() -> int:
    use_jp_font()
    import argparse
    ap = argparse.ArgumentParser(description='Hα 補正 ON/OFF 感度（近似）: EMスケール±αで ω_cut×残差の相関変化を表示')
    ap.add_argument('--name', required=True)
    ap.add_argument('--L-pc', type=float, default=100.0)
    ap.add_argument('--alpha', type=float, default=0.3, help='OFF側のEM増幅率（例: 0.3で+30%）')
    args = ap.parse_args()
    g = args.name.strip()
    em_p = Path(f'data/halpha/{g}/EM_pc_cm6.fits')
    vpath = Path(f'data/vel/{g}/velocity.fits')
    if not em_p.exists() or not vpath.exists():
        print('missing inputs'); return 0
    EM = fits.getdata(em_p).astype(float)
    V = fits.getdata(vpath).astype(float)
    # define two cases: ON (baseline scale=1.0), OFF (scale=1+alpha)
    r_on, p_on = corr_pair(EM, V, args.L_pc, scale=1.0)
    r_off, p_off = corr_pair(EM, V, args.L_pc, scale=1.0 + float(args.alpha))
    # simple HTML summary
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{g}: Hα 補正 ON/OFF 感度（近似）</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        f'<main class="wrap"><h1>{g}: Hα 補正 ON/OFF 感度（近似）</h1>',
        '<div class=card><p><small>近似方針: ON/OFF の差分を EM の一様スケール±α として近似し、ω_cut×残差の相関 (r,p) の変化を評価。</small><br>'
        f'<small>結果: ON: r={r_on:.3f}, p={p_on:.2e}／ OFF(×{1.0+args.alpha:.2f}): r={r_off:.3f}, p={p_off:.2e}</small></p></div>',
        '<div class=card><small>注意: 実際の減光/[NII]補正は空間変動を伴うため、ここでは<b>保守的な上振れ</b>として一様スケールを仮置き。主結論はON/OFFで共通な符号・傾向に基づいて提示する。</small></div>',
        '</main></body></html>'
    ]
    out = outdir / f'{g.lower()}_halpha_sensitivity.html'
    out.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

