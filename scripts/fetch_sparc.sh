#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch_sparc.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# SPARC 関連データの取得スクリプト
# 用法:
#   bash scripts/fetch_sparc.sh [mrt|zip|all]
# 既定は all（公式.mrtとZenodoのrotmod zipの両方を取得）

MODE=${1:-all}
OUTDIR=data/sparc
mkdir -p "$OUTDIR"

fetch_mrt() {
  local BASE="https://astroweb.cwru.edu/SPARC"
  echo "SPARC .mrt を取得中..."
  set -x
  curl -fL --retry 3 "$BASE/SPARC_Lelli2016c.mrt" \
    -o "$OUTDIR/SPARC_Lelli2016c.mrt"
  curl -fL --retry 3 "$BASE/MassModels_Lelli2016c.mrt" \
    -o "$OUTDIR/MassModels_Lelli2016c.mrt"
  set +x
  echo "保存: $OUTDIR/SPARC_Lelli2016c.mrt, MassModels_Lelli2016c.mrt"
}

fetch_zip() {
  local URL="https://zenodo.org/records/16284118/files/sparc_database.zip?download=1"
  echo "SPARC rotmod(zip) を取得中..."
  curl -fL --retry 3 "$URL" -o "$OUTDIR/sparc_database.zip"
  unzip -oq "$OUTDIR/sparc_database.zip" -d "$OUTDIR"
  echo "展開: $OUTDIR/sparc_database/*.dat"
}

case "$MODE" in
  mrt) fetch_mrt ;;
  zip) fetch_zip ;;
  all) fetch_mrt; fetch_zip ;;
  *) echo "不明なモード: $MODE (mrt|zip|all)" >&2; exit 2 ;;
esac
