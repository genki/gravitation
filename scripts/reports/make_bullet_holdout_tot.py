#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
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
from scipy.stats import pearsonr, spearmanr

from scripts.cluster.min_kernel import MinKernelParams, predict_kappa


def load_maps(root: Path):
    oc = root / 'omega_cut.fits'; se = root / 'sigma_e.fits'; ko = root / 'kappa_obs.fits'
    if not (oc.exists() and se.exists() and ko.exists()):
        return None
    try:
        ocv = fits.getdata(oc).astype(float); sev = fits.getdata(se).astype(float); kov = fits.getdata(ko).astype(float)
        pix = float(fits.getheader(se).get('PIXKPC', 1.0))
    except Exception:
        return None
    return ocv, sev, kov, pix


def main() -> int:
    ho_root = Path('data/cluster/Bullet')
    train_roots = [Path('data/cluster/Abell1689'), Path('data/cluster/CL0024')]
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)

    data = load_maps(ho_root)
    if data is None:
        (outdir / 'bullet_holdout_tot.html').write_text('<html><body><main class=wrap><div class=card><p>必要マップが不足</p></div></main></body></html>', encoding='utf-8')
        return 0
    oc, se, k_obs, pix = data
    # params
    pjson = Path('data/cluster/params_cluster.json')
    params = MinKernelParams()
    if pjson.exists():
        jd = json.loads(pjson.read_text(encoding='utf-8'))
        params = MinKernelParams(alpha=float(jd.get('alpha', 1.0)), beta=float(jd.get('beta', 0.0)), C=float(jd.get('C', 0.0)),
                                 xi=float(jd.get('xi', 0.0)), p=float(jd.get('p', 0.5)), tau_q=float(jd.get('tau_q', 0.7)),
                                 delta_tau_frac=float(jd.get('delta_tau_frac', 0.1)))
    k_pred = predict_kappa(oc, se, pix, params)
    if k_pred.shape != k_obs.shape:
        zy, zx = k_obs.shape[0]/k_pred.shape[0], k_obs.shape[1]/k_pred.shape[1]
        k_pred = ndi.zoom(k_pred, zoom=(zy, zx), order=1)
    # GR map
    kgr = None
    pgr = Path('data/cluster/gr/bullet_kappa_gr.npy')
    if pgr.exists():
        kgr0 = np.load(pgr)
        kgr = kgr0 if kgr0.shape == k_obs.shape else ndi.zoom(kgr0, zoom=(k_obs.shape[0]/kgr0.shape[0], k_obs.shape[1]/kgr0.shape[1]), order=1)
    if kgr is None:
        (outdir / 'bullet_holdout_tot.html').write_text('<html><body><main class=wrap><div class=card><p>κ_GR が未配置のため κ_tot を評価できません。</p></div></main></body></html>', encoding='utf-8')
        return 0
    k_tot = k_pred + kgr
    # residuals
    rr_fdb = (k_obs - k_pred)
    rr_tot = (k_obs - k_tot)
    # Σ_e to obs grid
    se_obs = se if se.shape == k_obs.shape else ndi.zoom(se, zoom=(k_obs.shape[0]/se.shape[0], k_obs.shape[1]/se.shape[1]), order=1)
    mm_f = np.isfinite(rr_fdb) & np.isfinite(se_obs)
    mm_t = np.isfinite(rr_tot) & np.isfinite(se_obs)
    s_f, p_f = spearmanr(rr_fdb[mm_f].ravel(), se_obs[mm_f].ravel(), nan_policy='omit') if np.any(mm_f) else (np.nan, np.nan)
    s_t, p_t = spearmanr(rr_tot[mm_t].ravel(), se_obs[mm_t].ravel(), nan_policy='omit') if np.any(mm_t) else (np.nan, np.nan)
    # top‑10%
    try:
        thr = float(np.nanquantile(se_obs[mm_f], 0.9))
        sel_f = mm_f & (se_obs >= thr); sel_t = mm_t & (se_obs >= thr)
        s_f90, p_f90 = spearmanr(rr_fdb[sel_f].ravel(), se_obs[sel_f].ravel(), nan_policy='omit') if np.any(sel_f) else (np.nan, np.nan)
        s_t90, p_t90 = spearmanr(rr_tot[sel_t].ravel(), se_obs[sel_t].ravel(), nan_policy='omit') if np.any(sel_t) else (np.nan, np.nan)
    except Exception:
        s_f90 = p_f90 = s_t90 = p_t90 = np.nan

    # panels
    try:
        vmin = np.nanpercentile(k_obs[np.isfinite(k_obs)], 2.5); vmax = np.nanpercentile(k_obs[np.isfinite(k_obs)], 97.5)
    except Exception:
        vmin, vmax = np.nanmin(k_obs), np.nanmax(k_obs)
    fig, axs = plt.subplots(2, 3, figsize=(10.8, 6.2))
    axs[0,0].imshow(k_pred, origin='lower', cmap='magma', vmin=vmin, vmax=vmax); axs[0,0].set_title('κ_FDB')
    axs[0,1].imshow(kgr, origin='lower', cmap='magma', vmin=vmin, vmax=vmax); axs[0,1].set_title('κ_GR')
    axs[0,2].imshow(k_tot, origin='lower', cmap='plasma', vmin=vmin, vmax=vmax); axs[0,2].set_title('κ_tot')
    axs[1,0].imshow(rr_fdb, origin='lower', cmap='coolwarm'); axs[1,0].set_title('R_FDB=κ_obs−κ_FDB')
    axs[1,1].imshow(rr_tot, origin='lower', cmap='coolwarm'); axs[1,1].set_title('R_tot=κ_obs−κ_tot')
    axs[1,2].imshow(k_obs, origin='lower', cmap='magma', vmin=vmin, vmax=vmax); axs[1,2].set_title('κ_obs')
    for ax in axs.ravel():
        ax.set_xlabel('x [pix]'); ax.set_ylabel('y [pix]')
    png = outdir / 'bullet_kappa_tot_overview.png'
    fig.tight_layout(); fig.savefig(png, dpi=140); plt.close(fig)

    rows = [
        ('global', s_f, p_f, s_t, p_t),
        ('top10%', s_f90, p_f90, s_t90, p_t90),
    ]
    tr = ''.join([f"<tr><td>{n}</td><td>{sf:.3f}</td><td>{pf:.2g}</td><td>{st:.3f}</td><td>{pt:.2g}</td></tr>" for n,sf,pf,st,pt in rows])
    html = [
        '<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>バレット: κ_tot 補助評価</title><link rel="stylesheet" href="../styles.css"></head><body>',
        '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a></nav></div></header>',
        '<main class="wrap"><h1>補助評価: κ_tot（κ_GR+κ_FDB）</h1>',
        f'<div class=card><p><img src="{png.name}" style="max-width:100%"></p></div>',
        '<div class=card><h3>残差×Σ_e Spearman（補助）</h3><table class="t"><thead><tr><th>ROI</th><th>R_FDB</th><th>p</th><th>R_tot</th><th>p</th></tr></thead>',
        f'<tbody>{tr}</tbody></table><small>注: 本ページは補助解析。主判定は FDB 対照とKPIのページに従う。</small></div>',
        '</main></body></html>'
    ]
    (outdir / 'bullet_holdout_tot.html').write_text('\n'.join(html), encoding='utf-8')
    print('wrote', outdir / 'bullet_holdout_tot.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
