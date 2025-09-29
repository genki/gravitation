#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/experiments/run_global_pass_sweep.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
OUT="$ROOT/server/public/reports/global_pass_sweep.json"
mkdir -p "$(dirname "$OUT")"

# Small exploratory sweep (FAST, no permutation) to rank candidates by top‑10% Spearman
# Allow env overrides like: ALPHAS="0.6,0.8" etc.
parse_list() { IFS=',' read -r -a arr <<<"$1"; printf '%s\n' "${arr[@]}"; }
if [ -n "${ALPHAS:-}" ]; then mapfile -t ALPHAS < <(parse_list "$ALPHAS"); else ALPHAS=(0.6 0.8 1.0); fi
if [ -n "${BETAS:-}" ]; then mapfile -t BETAS  < <(parse_list "$BETAS");  else BETAS=(0.5 0.7 0.8); fi
if [ -n "${XIS:-}" ]; then mapfile -t XIS     < <(parse_list "$XIS");     else XIS=(0.4 0.6 0.8); fi
if [ -n "${TAUQS:-}" ]; then mapfile -t TAUQS  < <(parse_list "$TAUQS");  else TAUQS=(0.45 0.50 0.55 0.60); fi

echo '[' >"$OUT"
first=1
for a in "${ALPHAS[@]}"; do
  for b in "${BETAS[@]}"; do
    for xi in "${XIS[@]}"; do
      for tq in "${TAUQS[@]}"; do
        jq -n --arg a "$a" --arg b "$b" --arg c "0.05" --arg xi "$xi" --arg p "1.0" --arg tq "$tq" '
          {alpha:($a|tonumber), beta:($b|tonumber), C:($c|tonumber), xi:($xi|tonumber), p:($p|tonumber), tau_q:($tq|tonumber)}
        ' > "$ROOT/data/cluster/params_cluster.json"
        FAST_HOLDOUT=1 BULLET_PERM_N=0 PYTHONPATH=. ./.venv/bin/python "$ROOT/scripts/reports/make_bullet_holdout.py" >/dev/null 2>&1 || true
        J="$ROOT/server/public/reports/bullet_holdout.json"
        if [ -f "$J" ]; then
          spear=$(jq -r '.indicators.strata.p90.spear_r // empty' "$J" 2>/dev/null || echo '')
          aicc=$(jq -r '.AICc.FDB // empty' "$J" 2>/dev/null || echo '')
          if [ -n "$spear" ]; then
            row=$(jq -n --argjson pa "$(cat "$ROOT/data/cluster/params_cluster.json")" --arg spear "$spear" --arg aicc "$aicc" '{params:$pa, spear_top10:($spear|tonumber), AICc_FDB:($aicc|tonumber)}')
            if [ $first -eq 0 ]; then echo ',' >>"$OUT"; fi
            first=0
            echo "$row" >>"$OUT"
          fi
        fi
      done
    done
  done
done
echo ']' >>"$OUT"
echo "wrote $OUT"
