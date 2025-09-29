#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import numpy as np
from src.toy.void_shells import accel_from_shell, sample_sphere_points


def fit_err_vs_ideal(r: np.ndarray, a_obs: np.ndarray) -> float:
    # Compare to ideal 1/r^2 with G*M=1
    target = 1.0 / (r ** 2)
    w = 1.0 / np.maximum(target, 1e-6)
    return float(np.mean(((a_obs - target) * w) ** 2))


def run_once(R: float, n_pts: int, rng: np.random.Generator) -> dict:
    r_grid = np.linspace(R*1.2, R*3.0, 50)
    a_true = accel_from_shell(r_grid, R_shell=R, n_pts=n_pts, mass_eff=1.0, rng=rng)
    err_true = fit_err_vs_ideal(r_grid, a_true)
    # Position randomized: randomize R (radius) substantially
    R_rand = float(R * rng.uniform(0.5, 1.5))
    a_randR = accel_from_shell(r_grid, R_shell=R_rand, n_pts=n_pts, mass_eff=1.0, rng=rng)
    err_randR = fit_err_vs_ideal(r_grid, a_randR)
    # Radius fixed but evaluate at permuted r values (as a rough proxy)
    perm = rng.permutation(len(r_grid))
    a_perm = a_true[perm]
    err_perm = fit_err_vs_ideal(r_grid, a_perm)
    return {
        'err_true': err_true,
        'err_randR': err_randR,
        'err_perm': err_perm,
        'delta_err_randR': err_randR - err_true,
        'delta_err_perm': err_perm - err_true,
    }


def main() -> int:
    rng = np.random.default_rng(123)
    R = 8.0
    n_pts = 4000
    trials = [run_once(R, n_pts, rng) for _ in range(30)]
    import statistics as st
    out = {
        'n': len(trials),
        'median_delta_randR': st.median([t['delta_err_randR'] for t in trials]),
        'median_delta_perm': st.median([t['delta_err_perm'] for t in trials]),
        'details': trials[:5],
    }
    Path('server/public/state_of_the_art').mkdir(parents=True, exist_ok=True)
    Path('server/public/state_of_the_art/early_universe_controls.json').write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8'
    )
    print('controls summary:', out)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

