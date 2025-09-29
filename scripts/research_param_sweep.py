#!/usr/bin/env python3
from __future__ import annotations
"""
Parameter sweep: effect of (ell0, m, lambda_an) on FDB anisotropic kernel profiles.
Outputs plots under server/public/assets/research/ and an HTML summary.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scripts.utils.mpl_fonts import use_jp_font
from pathlib import Path

def g_of_r(r, ell0, m=2):
    if ell0 <= 0:
        return np.zeros_like(r)
    return np.exp(- (np.abs(r)/ell0)**m)

def base_ar(r):
    eps=0.1
    return 1.0 / (r+eps)**2

def ar_fdb(r, ell0, m, lam):
    # thin-disk in-plane P2(0)=-1/2
    return base_ar(r) * (1.0 - 0.5 * lam * g_of_r(r, ell0, m))

def plot_sweep(R, param_sets, title, out_png):
    plt.figure(figsize=(5.6,3.6))
    for (ell0, m, lam) in param_sets:
        a = ar_fdb(R, ell0, m, lam)
        lbl = f"ℓ0={ell0}, m={m}, λ={lam}"
        plt.loglog(R+1e-3, a+1e-9, '-', lw=1.6, label=lbl)
    # refs
    ref = base_ar(R)
    plt.loglog(R+1e-3, ref, '--', lw=1.0, color='#555', label='~1/r² ref')
    plt.legend(fontsize=8)
    plt.title(title)
    plt.xlabel('r [kpc]'); plt.ylabel('|a_r| (arb.)')
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout(); plt.savefig(out_png, dpi=120); plt.close()

def main():
    use_jp_font()
    outdir = Path('server/public/assets/research')
    rep = Path('server/public/reports/fdb_param_sweep.html')
    R = np.linspace(0.2, 30.0, 400)
    sets1 = [(3.0, 2, 0.3), (5.0, 2, 0.3), (8.0, 2, 0.3)]
    sets2 = [(5.0, 2, 0.0), (5.0, 2, 0.3), (5.0, 2, 0.6)]
    sets3 = [(5.0, 2, 0.3), (5.0, 3, 0.3), (5.0, 4, 0.3)]
    plot_sweep(R, sets1, 'ℓ0 (kpc) sweep', outdir/'fdb_sweep_ell0.png')
    plot_sweep(R, sets2, 'λ_an sweep', outdir/'fdb_sweep_lambda.png')
    plot_sweep(R, sets3, 'm sweep', outdir/'fdb_sweep_m.png')
    # write simple report
    lines = [
        '<h1>FDB parameter sweep</h1>',
        '<figure class="card"><img src="../assets/research/fdb_sweep_ell0.png" style="max-width:100%;height:auto"><figcaption>ℓ0 sweep</figcaption></figure>',
        '<figure class="card"><img src="../assets/research/fdb_sweep_lambda.png" style="max-width:100%;height:auto"><figcaption>λ_an sweep</figcaption></figure>',
        '<figure class="card"><img src="../assets/research/fdb_sweep_m.png" style="max-width:100%;height:auto"><figcaption>m sweep</figcaption></figure>'
    ]
    Path(rep).parent.mkdir(parents=True, exist_ok=True)
    rep.write_text('\n'.join(lines), encoding='utf-8')
    print('wrote:', rep)

if __name__ == '__main__':
    main()
