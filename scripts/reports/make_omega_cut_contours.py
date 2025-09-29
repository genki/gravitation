#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
from astropy.io import fits


def em_to_ne_cm3(EM_pc_cm6: np.ndarray, L_pc: float) -> np.ndarray:
    # EM ≈ ∫ n_e^2 dl ≈ n_e^2 L  → n_e ≈ sqrt(EM/L)
    L = max(float(L_pc), 1.0)
    return np.sqrt(np.maximum(EM_pc_cm6, 0.0) / L)


def plasma_freq_rad_s(ne_cm3: np.ndarray) -> np.ndarray:
    # ω_p [rad/s] ≈ 5.64e4 * sqrt(n_e[cm^-3])
    return 5.64e4 * np.sqrt(np.maximum(ne_cm3, 0.0))


def main() -> int:
    ap = argparse.ArgumentParser(description='Make ω_cut≈ω_p contour PNG from EM map')
    ap.add_argument('--name', required=True, help='galaxy name (e.g., NGC3198)')
    ap.add_argument('--L-pc', type=float, default=100.0, help='assumed layer thickness [pc] for EM→n_e')
    ap.add_argument('--levels', type=str, default='1e3,3e3,1e4,3e4,1e5', help='ω_cut levels [rad/s], comma-separated')
    args = ap.parse_args()
    g = args.name.strip()
    em_p = Path(f'data/halpha/{g}/EM_pc_cm6.fits')
    if not em_p.exists():
        print('missing', em_p)
        return 0
    with fits.open(em_p) as hdul:
        em = np.asarray(hdul[0].data, dtype=float)
    ne = em_to_ne_cm3(em, args.L_pc)
    wcut = plasma_freq_rad_s(ne)
    # Basic contour plot
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scripts.utils.mpl_fonts import use_jp_font
    use_jp_font()
    fig, ax = plt.subplots(1, 1, figsize=(5.6, 3.8))
    ax.imshow(np.log10(np.maximum(ne, 1e-6)), origin='lower', cmap='gray', alpha=0.6)
    lv = [float(x) for x in args.levels.split(',') if x]
    cs = ax.contour(wcut, levels=lv, colors='C3', linewidths=0.8)
    ax.clabel(cs, inline=True, fontsize=8, fmt=lambda v: f'{v:.0e}')
    ax.set_title(f'{g}: ω_cut≈ω_p 等高線（rad/s）')
    ax.set_xticks([]); ax.set_yticks([])
    out = Path('server/public/reports') / f'{g.lower()}_omega_cut_contours.png'
    fig.tight_layout(); fig.savefig(out, dpi=140); plt.close(fig)
    print('wrote', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

