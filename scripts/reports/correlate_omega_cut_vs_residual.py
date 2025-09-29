#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from astropy.io import fits
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from scipy import stats, ndimage as ndi


def em_to_ne_cm3(EM_pc_cm6: np.ndarray, L_pc: float) -> np.ndarray:
    L = max(float(L_pc), 1.0)
    return np.sqrt(np.maximum(EM_pc_cm6, 0.0) / L)


def plasma_freq_rad_s(ne_cm3: np.ndarray) -> np.ndarray:
    return 5.64e4 * np.sqrt(np.maximum(ne_cm3, 0.0))


def gaussian_fft(img: np.ndarray, sigma_pix: float) -> np.ndarray:
    if sigma_pix <= 0: return img
    return ndi.gaussian_filter(img, sigma=float(sigma_pix))


def ring_median_residual(v: np.ndarray, nbins: int = 60) -> np.ndarray:
    ny, nx = v.shape
    yy, xx = np.indices((ny, nx))
    cy, cx = (ny - 1) / 2.0, (nx - 1) / 2.0
    r = np.hypot(xx - cx, yy - cy)
    rmax = r.max(); edges = np.linspace(0, rmax, nbins + 1)
    med = np.zeros_like(v) + np.nan
    for i in range(nbins):
        m = (r >= edges[i]) & (r < edges[i+1]) & np.isfinite(v)
        if not m.any():
            continue
        rv = np.nanmedian(v[m])
        med[m] = rv
    resid = v - med
    return resid


def match_resolution(src: np.ndarray, target_shape: tuple[int, int]) -> np.ndarray:
    sy, sx = src.shape; ty, tx = target_shape
    zoom = (ty / sy, tx / sx)
    return ndi.zoom(src, zoom=zoom, order=1)


def main() -> int:
    use_jp_font()
    ap = argparse.ArgumentParser(description='Correlation between omega_cut≈omega_p and velocity-field residuals')
    ap.add_argument('--name', required=True, help='galaxy name (e.g., NGC3198)')
    ap.add_argument('--L-pc', type=float, default=100.0, help='assumed layer thickness [pc]')
    ap.add_argument('--sigma-vel', type=float, default=0.0, help='optional Gaussian smoothing [pix] for velocity field')
    args = ap.parse_args()
    g = args.name.strip()
    # Load EM -> omega_cut
    em_p = Path(f'data/halpha/{g}/EM_pc_cm6.fits')
    if not em_p.exists():
        print('missing', em_p)
        return 0
    EM = fits.getdata(em_p).astype(float)
    # optional downsample for very large maps
    maxdim = max(EM.shape)
    if maxdim > 1200:
        scale = 800.0 / maxdim
        EM = ndi.zoom(EM, zoom=scale, order=1)
    ne = em_to_ne_cm3(EM, args.L_pc)
    wcut = plasma_freq_rad_s(ne)
    # Load velocity field and build residual
    vpath = Path(f'data/vel/{g}/velocity.fits')
    if not vpath.exists():
        print('missing', vpath)
        return 0
    V = fits.getdata(vpath).astype(float)
    if args.sigma_vel > 0:
        V = gaussian_fft(V, sigma_pix=float(args.sigma_vel))
    Vres = ring_median_residual(V)
    # downsample velocity residual if needed to limit memory
    if max(Vres.shape) > 1200:
        scale = 800.0 / max(Vres.shape)
        Vres = ndi.zoom(Vres, zoom=scale, order=1)
    # Match grids
    Vres_m = match_resolution(Vres, wcut.shape)
    # Build finite mask and compute Pearson r
    m = np.isfinite(wcut) & np.isfinite(Vres_m)
    # trim extremes (robust): drop top/bottom 1% of both axes
    if np.any(m):
        wx = np.log10(np.clip(wcut[m], 1e-8, None))
        wy = Vres_m[m]
        lx, hx = np.nanpercentile(wx, [1, 99]); ly, hy = np.nanpercentile(wy, [1, 99])
        m = m & (np.log10(np.clip(wcut, 1e-8, None))>=lx) & (np.log10(np.clip(wcut, 1e-8, None))<=hx) & (Vres_m>=ly) & (Vres_m<=hy)
    if not np.any(m):
        print('no overlap pixels')
        return 0
    x = np.log10(np.clip(wcut[m], 1e-8, None))  # log ω_cut for dynamic range
    y = Vres_m[m]
    n_eff = int(np.sum(m))
    if np.std(x) > 0 and np.std(y) > 0 and n_eff >= 8:
        r, p = stats.pearsonr(x, y)
    else:
        # fallback to Spearman if Pearson is degenerate
        if n_eff >= 8:
            r, p = stats.spearmanr(x, y)
        else:
            r, p = float('nan'), float('nan')
    # Scatter and maps
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    # Scatter
    fig, ax = plt.subplots(1,1, figsize=(5.2,3.8))
    ax.plot(x, y, ',', alpha=0.25)
    ax.set_xlabel('log10 ω_cut [rad/s]'); ax.set_ylabel('V_residual (arb.)')
    ax.set_title(f'{g}: 相関 r={r:.3f}, p={p:.2e} (N={n_eff})')
    scat = outdir / f'{g.lower()}_wcut_vs_vres_scatter.png'
    fig.tight_layout(); fig.savefig(scat, dpi=140); plt.close(fig)
    # Side-by-side maps
    fig, axs = plt.subplots(1,2, figsize=(8.4,3.6), constrained_layout=True)
    im0 = axs[0].imshow(np.log10(np.clip(wcut, 1e-8, None)), origin='lower', cmap='magma')
    axs[0].set_title('log ω_cut'); axs[0].set_xticks([]); axs[0].set_yticks([])
    fig.colorbar(im0, ax=axs[0], fraction=0.046, pad=0.04)
    vmax = np.nanpercentile(abs(Vres_m[m]), 95)
    im1 = axs[1].imshow(Vres_m, origin='lower', cmap='coolwarm', vmin=-vmax, vmax=vmax)
    axs[1].set_title('V_residual'); axs[1].set_xticks([]); axs[1].set_yticks([])
    fig.colorbar(im1, ax=axs[1], fraction=0.046, pad=0.04)
    maps = outdir / f'{g.lower()}_wcut_vs_vres_maps.png'
    fig.savefig(maps, dpi=140); plt.close(fig)
    # HTML report
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{g}: ω_cut × 残差 相関</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
        f'<main class="wrap"><h1>{g}: ω_cut（≈ω_p）と速度場残差の相関</h1>',
        f'<div class=card><p>相関: r={r:.3f}, p={p:.2e}（ピクセル単位; log ω_cut vs V_residual）</p>'
        '<p><small>EM→n_e（L≈100pc仮定）→ω_p。V_residual はリング中央値差し引き。解像度はEM側へ再サンプル。</small></p></div>',
        f'<div class=card><img src="{maps.name}" style="max-width:100%"></div>',
        f'<div class=card><img src="{scat.name}" style="max-width:100%"></div>',
        '</main></body></html>'
    ]
    out = outdir / f'{g.lower()}_wcut_corr.html'
    out.write_text('\n'.join(html), encoding='utf-8')
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
