#!/usr/bin/env python3
from __future__ import annotations

"""
Non-CLASS CMB/BAO compatibility proxy scan for Late-FDB.

We declare a parameter triple (eps_max, a_on, k_c) "allowed" if:
  1) CMB proxy: max_{k∈[1e-4, 0.3]} |μ(a_rec, k) − 1| < T_cmb
     with a_rec = 1/(1+1100). Also guard leakage up to a_drag≈1/1060*1.5.
  2) BAO proxy: avg_{a∈[0.33, 1.0]} avg_{k∈[0.02, 0.3]} |μ(a, k) − 1| < T_bao

Thresholds chosen conservatively for a Late turn-on:
  T_cmb = 5e-3, T_bao = 3e-2

This is a coarse proxy; a proper pipeline should validate with CLASS/CAMB.
"""

import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from src.cosmo.mu_late import mu_late


def cmb_bao_allowed(eps_max: float, a_on: float, da: float, k_c: float,
                    T_cmb: float = 5e-3, T_bao: float = 3e-2) -> bool:
    a_rec = 1.0 / 1101.0
    a_drag_hi = 1.0 / 1060.0 * 1.5
    # 1) CMB proxy at recombination
    k_cmb = np.geomspace(1e-4, 0.3, 200)
    MU_rec = mu_late(a_rec, k_cmb, eps_max=eps_max, a_on=a_on, da=da, k_c=k_c)
    dev_rec = float(np.max(np.abs(MU_rec - 1.0)))
    if dev_rec >= T_cmb:
        return False
    # Guard early leakage slightly after recombination
    a_leak = np.geomspace(a_rec, a_drag_hi, 50)
    MU_leak = mu_late(a_leak[:, None], k_cmb[None, :],
                      eps_max=eps_max, a_on=a_on, da=da, k_c=k_c)
    if float(np.max(np.abs(MU_leak - 1.0))) >= T_cmb:
        return False
    # 2) BAO proxy across late times and BAO band
    a_bao = np.linspace(0.33, 1.0, 60)
    k_bao = np.linspace(0.02, 0.3, 80)
    MU_bao = mu_late(a_bao[:, None], k_bao[None, :],
                     eps_max=eps_max, a_on=a_on, da=da, k_c=k_c)
    dev_bao = float(np.mean(np.abs(MU_bao - 1.0)))
    return dev_bao < T_bao


def scan_and_plot(cfg: dict, out_dir: Path) -> Path:
    eps_grid = np.linspace(0.0, 0.15, 31)
    kc_grid = np.linspace(0.05, 0.6, 23)
    a_on_list = [1/(1+z) for z in (30, 25, 20, 15, 10)]
    da = float(cfg.get('da', 0.02))
    allowed = np.zeros((len(a_on_list), len(eps_grid), len(kc_grid)), dtype=bool)
    for i, a_on in enumerate(a_on_list):
        for j, eps in enumerate(eps_grid):
            for k, kc in enumerate(kc_grid):
                allowed[i, j, k] = cmb_bao_allowed(eps, a_on, da, kc)
    # Plot: for each a_on, a panel in eps×k_c
    fig, axes = plt.subplots(1, len(a_on_list), figsize=(14, 3.2), sharey=True)
    for i, ax in enumerate(axes):
        im = ax.imshow(allowed[i].T[::-1, :], extent=(eps_grid[0], eps_grid[-1], kc_grid[0], kc_grid[-1]),
                       aspect='auto', origin='lower', cmap='Greens', vmin=0, vmax=1)
        z = int(round(1/a_on_list[i] - 1))
        ax.set_title(f'z_on≈{z}')
        ax.set_xlabel('eps_max')
        if i == 0:
            ax.set_ylabel('k_c')
    plt.suptitle('Fig‑EU1b: Allowed region (CMB/BAO proxy) — 1=allowed')
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'Fig-EU1b_bao_cmb_allowed.png'
    plt.savefig(out_path, dpi=160)
    plt.close()
    # Persist summary JSON
    meta = {
        'eps_grid': eps_grid.tolist(),
        'kc_grid': kc_grid.tolist(),
        'a_on_list': a_on_list,
        'allowed_any': bool(allowed.any()),
        'allowed_counts': allowed.sum(axis=(1,2)).tolist(),
        'thresholds': {'T_cmb': 5e-3, 'T_bao': 3e-2},
    }
    Path('server/public/state_of_the_art').mkdir(parents=True, exist_ok=True)
    Path('server/public/state_of_the_art/early_universe_bao_cmb.json').write_text(
        json.dumps(meta, indent=2), encoding='utf-8')
    return out_path


def main() -> int:
    cfg_p = Path('cfg/early_fdb.json')
    cfg = json.loads(cfg_p.read_text(encoding='utf-8')) if cfg_p.exists() else {
        'eps_max': 0.1, 'a_on': 1/21, 'da': 0.02, 'k_c': 0.2
    }
    out = scan_and_plot(cfg, Path('assets/figures/early_universe'))
    print('wrote scan:', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

