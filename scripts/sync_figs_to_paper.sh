#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/sync_figs_to_paper.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# assets/figures のSOTA画像を paper/figures へ同期する。
# 対象: 改善ヒスト, 散布図, 代表パネル, 共有比較(DDO154/161)

SRC=assets/figures
DST=paper/figures
mkdir -p "$DST"

# src_name:dst_name のリスト（bash3互換）
MAP=(
  "sota_improvement_hist.png:sota_improvement_hist.png"
  "sota_redchi2_scatter.png:sota_redchi2_scatter.png"
  "sota_vr_panel.png:sota_vr_panel.png"
  "sota_vr_panel_worst.png:sota_vr_panel_worst.png"
  "compare_fit_DDO154_shared.png:compare_fit_DDO154_shared.png"
  "compare_fit_DDO161_shared.png:compare_fit_DDO161_shared.png"
)

for pair in "${MAP[@]}"; do
  src=${pair%%:*}
  dst=${pair##*:}
  if [[ -f "$SRC/$src" ]]; then
    cp -f "$SRC/$src" "$DST/$dst"
  fi
done

echo "Synced figures to $DST"
