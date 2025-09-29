# Batch Scripts

This folder contains runnable scripts to reproduce the expanded grid runs described in the sprint memo.

Prereqs
- Python venv at `./.venv` with numpy/scipy/astropy/matplotlib installed.
- Data present under `data/cluster` as used by the repo.

Scripts
- `train_asinh_knee_multiscale.sh`: trains shared parameters over dtfrac list (default 0.10/0.15/0.20) with asinh Σ_e transform, multi‑scale interface gating, and W_eff knee.
- `search_beta.sh`: constrained β search on Bullet (keeps ΔAICc(FDB−shift) ≤ −10 and reports best β).
- `holdout_grid_asinh.sh`: full Bullet holdout with permutation/bootstrap across PSF/high‑pass grid, saving HTML/JSON snapshots.
- `run_full_asinh_grid.sh`: orchestrates the three steps above end‑to‑end.
- `run_coarse_asinh_grid.sh`: fast coarse pass (single dtfrac, reduced grids, PERM=512/BOOT=0). Use this to get a quick ETA and trend.

Usage
```
chmod +x batch/*.sh

# End‑to‑end run (asinh + knee + multiscale)
batch/run_full_asinh_grid.sh

# Or run steps manually
batch/train_asinh_knee_multiscale.sh         # optional: pass custom dt list, e.g. 0.10 0.20
batch/search_beta.sh
batch/holdout_grid_asinh.sh 6 7 9           # high‑pass sigmas to evaluate

# Quick coarse run (~45–75 min on 4 vCPU)
batch/run_coarse_asinh_grid.sh
```

Config overrides
- Copy `batch/config.env.example` to `batch/config.env` and edit values.
