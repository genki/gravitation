#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from astropy.io import fits
from scipy import ndimage as ndi, stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from theory.info_decoherence import EtaParams
from src.fdb.a_from_info import info_bias_vector_from_map
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
    edges = np.linspace(0.0, r.max(), nbins + 1)
    med = np.full_like(v, np.nan, dtype=float)
    for i in range(nbins):
        m = (r >= edges[i]) & (r < edges[i+1]) & np.isfinite(v)
        if m.any():
            med[m] = np.nanmedian(v[m])
    return v - med


def weighted_pearsonr(x: np.ndarray, y: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    w = np.asarray(w, float)
    w /= np.nansum(w) + 1e-12
    xm = np.nansum(w * x)
    ym = np.nansum(w * y)
    xc = x - xm; yc = y - ym
    cov = np.nansum(w * xc * yc)
    vx = np.nansum(w * xc * xc)
    vy = np.nansum(w * yc * yc)
    r = cov / (np.sqrt(vx * vy) + 1e-18)
    # effective n for p-value (approx): neff = (sum w)^2 / sum w^2
    neff = (1.0) ** 2 / (np.nansum(w * w) + 1e-12)
    if neff > 3:
        t = r * np.sqrt(max(neff - 2.0, 1.0) / max(1.0 - r * r, 1e-12))
        p = 2.0 * (1.0 - stats.t.cdf(abs(t), df=max(neff - 2.0, 1.0)))
    else:
        p = np.nan
    return float(r), float(p)


def main() -> int:
    use_jp_font()
    ap = argparse.ArgumentParser(description='Env toggle: W=1 vs W(n_e,ω_cut) for angle/correlation metrics')
    ap.add_argument('--name', required=True)
    ap.add_argument('--L-pc', type=float, default=100.0)
    ap.add_argument('--alpha', type=float, default=1.0, help='weight strength for W=exp(-alpha * (ω/med))')
    ap.add_argument('--beta', type=float, default=0.3, help='info-flow anisotropy β')
    ap.add_argument('--s-kpc', type=float, default=0.5)
    ap.add_argument('--sgk', type=float, default=0.6)
    args = ap.parse_args()
    g = args.name.strip()
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)

    # Load EM -> ω_cut
    em_p = Path(f'data/halpha/{g}/EM_pc_cm6.fits')
    vpath = Path(f'data/vel/{g}/velocity.fits')
    if not em_p.exists() or not vpath.exists():
        print('missing inputs', em_p, vpath)
        return 0
    EM = fits.getdata(em_p).astype(float)
    if max(EM.shape) > 1200:
        EM = ndi.zoom(EM, zoom=800.0/max(EM.shape), order=1)
    ne = em_to_ne_cm3(EM, args.L_pc)
    wcut = plasma_freq_rad_s(ne)

    # Velocity residuals (rebinned to EM grid)
    V = fits.getdata(vpath).astype(float)
    if max(V.shape) > 1200:
        V = ndi.zoom(V, zoom=800.0/max(V.shape), order=1)
    Vres = ring_median_residual(V)
    Vres = ndi.zoom(Vres, zoom=(EM.shape[0]/Vres.shape[0], EM.shape[1]/Vres.shape[1]), order=1)

    # Info-flow a_FDB vector from EM map
    pix_kpc = 0.2
    k_grid = np.linspace(0.02, 1.0, 20)
    phi_k = np.exp(-(k_grid/args.sgk)**2)
    ax, ay = info_bias_vector_from_map(EM, pix_kpc=pix_kpc, k_grid=k_grid, phi_k=phi_k,
                                       eta_params=EtaParams(beta=args.beta, s_kpc=args.s_kpc))
    # ∇ω_cut (rebinned on the same grid already)
    gy, gx = np.gradient(wcut, pix_kpc)
    amag = np.hypot(ax, ay)
    gmag = np.hypot(gx, gy)
    m0 = np.isfinite(wcut) & np.isfinite(Vres) & np.isfinite(amag) & (gmag > 0) & (amag > 0)
    if not m0.any():
        print('no finite pixels for metrics')
        return 0

    # Weight map W based on ω_cut (dimensionless by median)
    med_w = float(np.nanmedian(wcut[m0])) or 1.0
    W = np.exp(-float(args.alpha) * (wcut / med_w))
    W = np.clip(W, 1e-6, 1.0)

    # Angles between a_FDB and ∇ω_cut
    axu = ax / (amag + 1e-12)
    ayu = ay / (amag + 1e-12)
    gxu = gx / (gmag + 1e-12)
    gyu = gy / (gmag + 1e-12)
    dot = np.clip(axu*gxu + ayu*gyu, -1.0, 1.0)
    th = np.arccos(dot)
    # Subset to stronger a_FDB half to stabilize
    strong = amag >= np.nanmedian(amag[m0])
    m = m0 & strong
    thv = th[m]
    Wv = W[m]

    # Angle stats (OFF and ON)
    def angle_stats(theta: np.ndarray, w: np.ndarray | None = None) -> tuple[float, float, int]:
        if theta.size < 10:
            return float('nan'), float('nan'), int(theta.size)
        if w is None:
            mdeg = float(np.degrees(np.nanmean(np.abs(theta))))
            R = float(np.hypot(np.nanmean(np.cos(theta)), np.nanmean(np.sin(theta))))
            return mdeg, R, int(theta.size)
        w = w.astype(float); w /= np.nansum(w) + 1e-12
        mdeg = float(np.degrees(np.nansum(w * np.abs(theta))))
        C = float(np.nansum(w * np.cos(theta)))
        S = float(np.nansum(w * np.sin(theta)))
        R = float(np.hypot(C, S))
        return mdeg, R, int(theta.size)

    ang_off = angle_stats(thv, None)
    ang_on  = angle_stats(thv, Wv)

    # Correlations (log ω_cut vs residual)
    x = np.log10(np.clip(wcut[m0], 1e-8, None))
    y = Vres[m0]
    r_off, p_off = stats.pearsonr(x, y) if (np.std(x)>0 and np.std(y)>0 and x.size>5) else (np.nan, np.nan)
    r_on, p_on   = weighted_pearsonr(x, y, W[m0])

    # Figures: angle hist OFF/ON
    def save_angle_hist(theta: np.ndarray, w: np.ndarray | None, title: str, out: Path):
        fig, axp = plt.subplots(1,1, figsize=(5.0,3.4))
        tbins = np.linspace(0, np.pi, 37)
        if w is None:
            axp.hist(np.degrees(theta), bins=36, range=(0,180), color='#4477aa', alpha=0.8)
        else:
            # weighted histogram
            h, be = np.histogram(theta, bins=tbins, weights=w)
            axp.bar(0.5*(be[1:]+be[:-1]) * 180/np.pi, h, width=(be[1]-be[0]) * 180/np.pi, color='#aa7744', alpha=0.8)
        axp.set_xlabel('angle(∇ω_cut, a_FDB) [deg]'); axp.set_ylabel('count (arb)')
        axp.set_title(title)
        fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)

    png_ang_off = outdir / f'{g.lower()}_angle_hist_off.png'
    png_ang_on  = outdir / f'{g.lower()}_angle_hist_on.png'
    save_angle_hist(thv, None, f'W=1: mean|θ|≈{ang_off[0]:.1f}°, R≈{ang_off[1]:.2f}, n={ang_off[2]}', png_ang_off)
    save_angle_hist(thv, Wv,  f'W=ON: mean|θ|≈{ang_on[0]:.1f}°, R≈{ang_on[1]:.2f}, n={ang_on[2]}',  png_ang_on)

    # Scatter OFF/ON
    def save_scatter(x: np.ndarray, y: np.ndarray, w: np.ndarray | None, title: str, out: Path):
        fig, ax = plt.subplots(1,1, figsize=(5.2,3.6))
        if w is None:
            ax.plot(x, y, ',', alpha=0.25)
        else:
            # alpha scale by weight quantiles
            wq = (w - np.nanmin(w)) / (np.nanmax(w) - np.nanmin(w) + 1e-12)
            ax.scatter(x, y, s=2, c=wq, cmap='viridis', alpha=0.35)
        ax.set_xlabel('log10 ω_cut [rad/s]'); ax.set_ylabel('V_residual (arb.)')
        ax.set_title(title)
        fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)

    png_scat_off = outdir / f'{g.lower()}_wcut_vs_vres_scatter_off.png'
    png_scat_on  = outdir / f'{g.lower()}_wcut_vs_vres_scatter_on.png'
    save_scatter(x, y, None, f'W=1: r={r_off:.3f}, p={p_off:.2e}', png_scat_off)
    save_scatter(x, y, W[m0], f'W=ON: r_w={r_on:.3f}, p≈{p_on:.2e}', png_scat_on)

    # Weight map thumbnail
    png_W = outdir / f'{g.lower()}_W_map.png'
    fig, axw = plt.subplots(1,1, figsize=(4.0,3.2))
    im = axw.imshow(W, origin='lower', cmap='plasma'); axw.set_title('W(n_e,ω_cut)'); axw.set_xticks([]); axw.set_yticks([])
    plt.colorbar(im, ax=axw, fraction=0.046, pad=0.04)
    fig.tight_layout(); fig.savefig(png_W, dpi=140); plt.close(fig)

    # HTML with toggle
    html = []
    html.append('<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">')
    html.append(f'<title>{g}: Wトグル（環境OFF/ON）</title><link rel="stylesheet" href="../styles.css">')
    html.append('<style>.toggle-btn{margin:6px 6px 12px 0;padding:6px 10px;border:1px solid #888;cursor:pointer;border-radius:4px;} .active{background:#eee;}</style>')
    html.append('</head><body>')
    html.append('<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>')
    html.append(f'<main class="wrap"><h1>{g}: W(n_e, ω_cut) トグル</h1>')
    html.append('<div class=card><p><small>W=1 は公平比較の既定。W=ON は ω_cut を基にした環境重み（W=exp[−α·(ω/median ω)]）。AICc/rχ² は回転曲線適合（W非依存）であり、本トグルは相関・角度統計の重み付けに限定。</small></p></div>')
    html.append('<div class=card>')
    html.append('<button class="toggle-btn active" id="btnOff">W=1（環境OFF）</button>')
    html.append('<button class="toggle-btn" id="btnOn">W=ON（環境ON）</button>')
    html.append('</div>')
    # OFF block
    html.append('<div id="blkOff">')
    html.append(f'<div class=card><p><b>角度整合</b>: mean|θ|≈{ang_off[0]:.1f}°, R≈{ang_off[1]:.2f}, n={ang_off[2]}</p>')
    html.append(f'<p><img src="{png_ang_off.name}" style="max-width:100%"></p></div>')
    html.append(f'<div class=card><p><b>強度相関</b>: r={r_off:.3f}, p={p_off:.2e}</p>')
    html.append(f'<p><img src="{png_scat_off.name}" style="max-width:100%"></p></div>')
    html.append('</div>')
    # ON block
    html.append('<div id="blkOn" style="display:none">')
    html.append(f'<div class=card><p><b>角度整合（重み付け）</b>: mean|θ|≈{ang_on[0]:.1f}°, R≈{ang_on[1]:.2f}, n={ang_on[2]}</p>')
    html.append(f'<p><img src="{png_ang_on.name}" style="max-width:100%"></p></div>')
    html.append(f'<div class=card><p><b>強度相関（重み付け）</b>: r_w={r_on:.3f}, p≈{p_on:.2e}</p>')
    html.append(f'<p><img src="{png_scat_on.name}" style="max-width:100%"></p></div>')
    html.append(f'<div class=card><p><b>Wマップ</b></p><p><img src="{png_W.name}" style="max-width:100%"></p></div>')
    html.append('</div>')
    # JS
    html.append('<script>const off=document.getElementById("blkOff"), on=document.getElementById("blkOn"), bo=document.getElementById("btnOff"), bn=document.getElementById("btnOn"); function setOn(x){ if(x){on.style.display="";off.style.display="none";bn.classList.add("active");bo.classList.remove("active");}else{on.style.display="none";off.style.display="";bo.classList.add("active");bn.classList.remove("active");}} bo.onclick=()=>setOn(false); bn.onclick=()=>setOn(true);</script>')
    html.append('</main></body></html>')
    (outdir / f'{g.lower()}_env_toggle.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote', outdir / f'{g.lower()}_env_toggle.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

