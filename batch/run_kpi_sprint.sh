#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run batch/run_kpi_sprint.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
source "$HERE/_common.sh"

# Load optional overrides
if [[ -f "$HERE/config.env" ]]; then
  # shellcheck disable=SC1090
  source "$HERE/config.env"
fi

# Grids per directive
TAUQS="0.70,0.75,0.80"
DTFRACS="0.10 0.15 0.20"
S_GATES="12,16,24,32"
GATE_SIGMAS="2,4,8"
Q_KNEE="0.6,0.7,0.8"
XI="1.2,2.4,3.6"
XI_SAT="1.0,0.5,0.3333"
P_LIST="0.7,1.0,1.3"
BETAS="0.4,0.6,0.8,1.0"
PSF_LIST="1.2,1.5,1.8"
HP_LIST=(6 8 10)

# Permutation / Bootstrap rigor
export BULLET_PERM_N=${BULLET_PERM_N:-5000}
export BULLET_BOOT_N=${BULLET_BOOT_N:-4096}

start_ts=$(date +%s)
for SE in asinh log1p rank; do
  echo "[kpi-sprint] === SE_TRANSFORM=$SE ==="
  export SE_TRANSFORM=$SE
  export GATE_SIGMAS=$GATE_SIGMAS
  export GRID_TAUQ=$TAUQS
  export GRID_DELTA_TAU_FRAC="0.10"  # placeholder; looped by train script via DT list
  export GRID_S_GATE=$S_GATES
  export GRID_Q_KNEE=$Q_KNEE
  export GRID_XI=$XI
  export GRID_XI_SAT=$XI_SAT
  export GRID_P=$P_LIST
  # Slightly stronger encouragement for negative Spearman during training
  export W_CORR_FRAC=${W_CORR_FRAC:-0.20}

  # Train shared params across dtfrac list
  PYTHONUNBUFFERED=1 "$HERE/train_asinh_knee_multiscale.sh" $DTFRACS

  # Constrained beta search
  GRID_BETA=$BETAS PYTHONUNBUFFERED=1 "$HERE/search_beta.sh"

  # Holdout across HP list with full PSF/BETA sweep
  export BETA_SWEEP=$BETAS
  export PSF_LIST=$PSF_LIST
  for HP in "${HP_LIST[@]}"; do
    PYTHONUNBUFFERED=1 "$HERE/holdout_grid_asinh.sh" "$HP"
  done
done

# Update SOTA summary
PYTHONUNBUFFERED=1 python -u "$REPO_ROOT/scripts/reports/update_sota.py" || true

elapsed=$(( $(date +%s) - start_ts ))
printf '[kpi-sprint] completed in %dm\n' "$((elapsed/60))"
