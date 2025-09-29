#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.cosmo.mu_late import mu_late
from src.cosmo.growth_solver import growth_factor, Cosmology
from src.toy.void_shells import accel_from_shell
from src.astro.uvlf_boost import grid_for_plot
from scripts.eu.bao_cmb_scan import scan_and_plot as bao_cmb_scan
from scripts.eu.fig_21cm_corr import generate_eu5
from scripts.eu.class_validate import main as run_class_validate


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:12]


def ensure_outdir() -> Path:
    out = Path('assets/figures/early_universe')
    out.mkdir(parents=True, exist_ok=True)
    return out


def fig_eu1_mu_late_contour(cfg: dict) -> Path:
    out = ensure_outdir() / 'Fig-EU1_mu_late_contour.png'
    a = np.geomspace(1/100.0, 1.0, 120)  # z~99 → 0
    k = np.geomspace(1e-3, 10.0, 160)
    MU = mu_late(a[:, None], k[None, :],
                 eps_max=float(cfg['eps_max']),
                 a_on=float(cfg['a_on']),
                 da=float(cfg['da']),
                 k_c=float(cfg['k_c']))
    plt.figure(figsize=(6, 4))
    cs = plt.contourf(k, a, MU, levels=20, cmap='viridis')
    plt.colorbar(cs, label='mu_late(a,k)')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('k [arb]')
    plt.ylabel('a')
    plt.title('Fig-EU1: mu_late(a,k)')
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    plt.close()
    return out


def fig_eu2_growth_ratio(cfg: dict) -> Path:
    out = ensure_outdir() / 'Fig-EU2_growth_ratio.png'
    a = np.geomspace(1/40.0, 1.0, 200)
    cosmo = Cosmology()
    D_base = growth_factor(a, k=1.0, cosmo=cosmo, use_mu_late=False)
    D_late = growth_factor(a, k=1.0, cosmo=cosmo, use_mu_late=True,
                           eps_max=float(cfg['eps_max']), a_on=float(cfg['a_on']),
                           da=float(cfg['da']), k_c=float(cfg['k_c']))
    plt.figure(figsize=(6, 4))
    plt.plot(1/a - 1, D_late / D_base, label='D_late/D_LCDM')
    plt.xscale('log')
    plt.gca().invert_xaxis()
    plt.xlabel('z')
    plt.ylabel('D_late / D_LCDM')
    plt.title('Fig-EU2: Growth boost (z≈30→6)')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    plt.close()
    return out


def fig_eu4_shell_field() -> Path:
    out = ensure_outdir() / 'Fig-EU4_shell_field.png'
    R = 10.0
    r_out = np.linspace(R*1.1, R*4.0, 60)
    r_in = np.linspace(0.5, R*0.9, 40)
    a_out = accel_from_shell(r_out, R_shell=R, n_pts=4096, mass_eff=1.0)
    a_in = accel_from_shell(r_in, R_shell=R, n_pts=4096, mass_eff=1.0)
    # Ideal outside: GM/r^2 with G*M=1
    a_out_ideal = 1.0 / (r_out ** 2)
    plt.figure(figsize=(6, 4))
    plt.loglog(r_out, a_out, 'C0.', label='|a_out| (MC)')
    plt.loglog(r_out, a_out_ideal, 'k--', label='1/r^2')
    plt.loglog(r_in, np.maximum(a_in, 1e-8), 'C1.', label='|a_in| (MC)')
    plt.xlabel('r')
    plt.ylabel('|a(r)|')
    plt.title('Fig-EU4: Shell field — outside ~1/r^2, inside ~0')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out, dpi=160)
    plt.close()
    return out


def main() -> int:
    cfg_p = Path('cfg/early_fdb.json')
    cfg = json.loads(cfg_p.read_text(encoding='utf-8')) if cfg_p.exists() else {
        'eps_max': 0.1, 'a_on': 1/21, 'da': 0.02, 'k_c': 0.2
    }
    sha = _sha256_bytes(json.dumps(cfg, sort_keys=True).encode('utf-8'))
    out1 = fig_eu1_mu_late_contour(cfg)
    out2 = fig_eu2_growth_ratio(cfg)
    # Fig‑EU3: UVLF bright-end multiplier grid
    out3 = ensure_outdir() / 'Fig-EU3_uvlf_multiplier.png'
    nu, dr, R = grid_for_plot()
    plt.figure(figsize=(6, 4))
    for i, r in enumerate(dr):
        plt.semilogy(nu, R[i], 'o-', label=f'D\'/D={r:.2f}')
    plt.xlabel('ν (peak height)')
    plt.ylabel('n\' / n')
    plt.title('Fig-EU3: UVLF bright-end multiplier')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out3, dpi=160)
    plt.close()
    out4 = fig_eu4_shell_field()
    # Fig‑EU1b: BAO/CMB allowed region (proxy)
    out1b = bao_cmb_scan(cfg, ensure_outdir())
    # Fig‑EU5: 21 cm |∇Tb| × galaxy correlation (concept)
    out5 = generate_eu5(ensure_outdir())
    # Fig‑EU1c: CLASS 連携（あれば実行; なければプレースホルダ）
    try:
        run_class_validate()
    except Exception:
        pass
    # Compute growth→UVLF stats at selected redshifts and ν
    z_list = [15, 12, 10]
    a_list = [1/(1+z) for z in z_list]
    cosmo = Cosmology()
    stats = []
    for aZ, z in zip(a_list, z_list):
        a_grid = np.geomspace(aZ/8.0, aZ, 256)
        D0 = growth_factor(a_grid, k=1.0, cosmo=cosmo, use_mu_late=False)
        D1 = growth_factor(a_grid, k=1.0, cosmo=cosmo, use_mu_late=True,
                           eps_max=float(cfg['eps_max']), a_on=float(cfg['a_on']),
                           da=float(cfg['da']), k_c=float(cfg['k_c']))
        ratio = float(D1[-1] / max(D0[-1], 1e-12))
        # Rare-tail multipliers for ν=3..6
        nu = np.array([3.0, 4.0, 5.0, 6.0])
        _, _, R = grid_for_plot(nu_vals=nu, D_ratios=(ratio,))
        stats.append({'z': z, 'D_ratio': ratio, 'nu': nu.tolist(), 'mult': R[0].tolist()})
    meta = {
        'cfg_path': str(cfg_p), 'cfg_sha12': sha,
        'figs': [str(out1), str(out2), str(out3), str(out4), str(out1b), str(out5)]
    }
    Path('server/public/state_of_the_art').mkdir(parents=True, exist_ok=True)
    Path('server/public/state_of_the_art/early_universe_meta.json').write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    Path('server/public/state_of_the_art/early_universe_stats.json').write_text(
        json.dumps({'z_stats': stats}, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    print('wrote figures:', meta)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
