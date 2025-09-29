#!/usr/bin/env python3
from __future__ import annotations
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from fdb.angle_kernels import K_lambert_forward


def main() -> int:
    use_jp_font()
    out_img = Path('assets/figures/boundary'); out_img.mkdir(parents=True, exist_ok=True)
    cos = np.linspace(0, 1, 400)
    for chi in [0.0, 0.25, 1.0]:
        K = K_lambert_forward(cos, chi)
        plt.plot(np.arccos(cos)*180/np.pi, K, label=f'χ={chi}')
    plt.xlabel('θ [deg]'); plt.ylabel('K(θ;χ)'); plt.grid(True, ls=':', alpha=0.4); plt.legend(frameon=False)
    p = out_img / 'kernel_shapes.png'
    plt.tight_layout(); plt.savefig(p, dpi=160); plt.close()
    # Simple HTML
    out_html = Path('server/public/reports/boundary_demo.html'); out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(f'<html><body><h1>緩やかな境界と垂直放射：角度核</h1><p><img src="../{p}" style="max-width:100%"></p></body></html>', encoding='utf-8')
    print('wrote', out_html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
