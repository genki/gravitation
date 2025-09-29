#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/sync_figs_to_docs.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

SRC=assets/figures
DST=docs/img
mkdir -p "$DST"

LIST=(
  sota_improvement_hist.png
  sota_redchi2_scatter.png
  sota_vr_panel.png
  sota_vr_panel_worst.png
  compare_fit_DDO154_shared.png
  compare_fit_DDO161_shared.png
)

for f in "${LIST[@]}"; do
  if [[ -f "$SRC/$f" ]]; then
    cp -f "$SRC/$f" "$DST/$f"
  fi
done

echo "Synced figures to $DST"
