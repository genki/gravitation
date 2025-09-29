#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run batch/run_coarse_asinh_grid.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/_common.sh"

# Coarse overrides (runtime ≈ 45–75 min on this 4‑vCPU box)
export W_CORR_FRAC=${W_CORR_FRAC:-0.08}
export SE_TRANSFORM=${SE_TRANSFORM:-asinh}
export GATE_SIGMAS=${GATE_SIGMAS:-4}
export GRID_S_GATE=${GRID_S_GATE:-16}
export GRID_Q_KNEE=${GRID_Q_KNEE:-0.7}
export GRID_XI=${GRID_XI:-2.4}
export GRID_XI_SAT=${GRID_XI_SAT:-0.5}
export GRID_P=${GRID_P:-1.0}
export GRID_TAUQ=${GRID_TAUQ:-0.75}
export GRID_DELTA_TAU_FRAC=${GRID_DELTA_TAU_FRAC:-0.15}
export GRID_BETA=${GRID_BETA:-0.8}

# Holdout (quick) — can later bump to PERM_N=5000/BOOT_N=4096 for final
export PSF_LIST=${PSF_LIST:-1.5}
export BETA_SWEEP=${BETA_SWEEP:-0.6,0.8}
export BULLET_W_POWER_FORCE=${BULLET_W_POWER_FORCE:-0.1}
export BULLET_PERM_N=${BULLET_PERM_N:-512}
export BULLET_BOOT_N=${BULLET_BOOT_N:-0}

start_ts=$(date +%s)

# 1) Train on a single dtfrac for speed
"$HERE/train_asinh_knee_multiscale.sh" 0.15

# 2) Constrained β search
"$HERE/search_beta.sh"

# 3) Holdout at HP=7 (quick)
"$HERE/holdout_grid_asinh.sh" 7

elapsed=$(( $(date +%s) - start_ts ))
printf '[coarse] completed in %dm\n' "$((elapsed/60))"
