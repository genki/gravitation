#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main() -> int:
    ap = argparse.ArgumentParser(description='Overlay Solar-System upper bound as half-plane in (κ,C) with kappaC_fit.json')
    ap.add_argument('--file', type=Path, default=Path('data/results/kappaC_fit.json'))
    ap.add_argument('--amax', type=float, default=1e-12, help='|a_FDB| upper bound [km^2 s^-2 kpc^-1] at 1–5 AU (proxy units)')
    ap.add_argument('--Kc', type=float, default=1.0, help='Normalization coefficient for 1/r term at AU-scale (unknown → set 1.0)')
    ap.add_argument('--Kif', type=float, default=0.0, help='Normalization for info-flow term at AU-scale (often negligible)')
    args = ap.parse_args()
    p = args.file
    if not p.exists():
        print('missing', p)
        return 0
    data = json.loads(p.read_text(encoding='utf-8'))
    outdir = Path('server/public/reports'); outdir.mkdir(parents=True, exist_ok=True)
    for row in data:
        if not isinstance(row, dict) or not row.get('ok'): continue
        name = row.get('name', 'unknown')
        kappa = float(row.get('kappa', 0.0)); C = float(row.get('C', 0.0))
        # Build half-plane: Kif*κ + Kc*C ≤ amax
        Kc = float(args.Kc); Kif = float(args.Kif); amax = float(args.amax)
        # Plot
        fig, ax = plt.subplots(1,1, figsize=(5.0,4.0))
        # ellipse image if exists
        png = outdir / f'{name.lower()}_kappaC_ellipse.png'
        if png.exists():
            from matplotlib.offsetbox import AnnotationBbox, OffsetImage
            import matplotlib.image as mpimg
            img = mpimg.imread(str(png))
            ax.imshow(img, extent=[-0.1,1.0,-0.1,1.0], aspect='auto', alpha=0.08)
        xs = np.linspace(0, max(1.5*kappa, 1.0), 200)
        if Kc > 0:
            ys = (amax - Kif*xs) / max(Kc, 1e-30)
        else:
            ys = np.full_like(xs, np.nan)
        ax.plot(xs, ys, 'r--', label=f'{Kif:.2g}·κ+{Kc:.2g}·C≤{amax:.1e}')
        ax.fill_between(xs, -1, ys, color='r', alpha=0.1)
        ax.plot([kappa], [C], 'ko', ms=4, label='fit')
        ax.set_xlim(left=0); ax.set_ylim(bottom=0)
        ax.set_xlabel('κ'); ax.set_ylabel('C'); ax.set_title(f'{name}: Solar上限の半平面（規格化: 任意 K）')
        ax.legend(frameon=False, fontsize=8)
        out = outdir / f'{name.lower()}_kappaC_with_solar_bound.png'
        fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
        # HTML wrap
        html = ['<html lang="ja-JP"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
                f'<title>{name}: κ,C と Solar上限</title><link rel="stylesheet" href="../styles.css"></head><body>',
                '<header class="site-header"><div class="wrap"><div class="brand">研究進捗</div><nav class="nav"><a href="../index.html">レポート</a><a href="../state_of_the_art/index.html">SOTA</a></nav></div></header>',
                f'<main class="wrap"><h1>{name}: κ,C と Solar-System 上限（半平面）</h1>',
                f'<div class=card><p>仮定: K_if={Kif:.2g}, K_c={Kc:.2g}, |a_FDB|≤{amax:.1e}（単位: km² s⁻² kpc⁻¹ 相当）</p>'
                '<p><small>注: K_if, K_c はAUスケールの規格化係数（既知でなければ K_c=1, K_if≈0）。可視化の目的で半平面の傾きを提示。</small></p></div>',
                f'<div class=card><img src="{out.name}" style="max-width:100%"></div>',
                '</main></body></html>']
        (outdir / f'{name.lower()}_kappaC_solar.html').write_text('\n'.join(html), encoding='utf-8')
        print('wrote', outdir / f'{name.lower()}_kappaC_solar.html')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

