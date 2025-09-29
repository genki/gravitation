#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/download_manga_dr17.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# MaNGA DR17 の LOGCUBE/MAPS ダウンローダ
# 使い方:
#   scripts/download_manga_dr17.sh [plateifu_file]
#
# plateifu_file の既定は data/manga/dr17/plateifu.txt
# 出力構成:
#   data/manga/dr17/<plateifu>/{LOGCUBE,MAPS}/*.fits.gz

PLATEIFU_FILE=${1:-data/manga/dr17/plateifu.txt}
ROOT=data/manga/dr17

if [[ ! -f "$PLATEIFU_FILE" ]]; then
  echo "plateifu ファイルが見つかりません: $PLATEIFU_FILE" >&2
  exit 1
fi

mkdir -p "$ROOT"

# 注意: DR17 MaNGA の公開 SAS エンドポイント。パスは変更される場合があります。
# DR17のDAP 3.1.0 + SPX-MILESHC-MASTARSSP 構成に対応
# 参考: spectro/analysis/v3_1_1/3.1.0/SPX-MILESHC-MASTARSSP/
# LOGCUBE: .../{plate}/{ifudsgn}/manga-{plateifu}-LOGCUBE-SPX-MILESHC-MASTARSSP.fits.gz
# MAPS   : .../{plate}/{ifudsgn}/manga-{plateifu}-MAPS-SPX-MILESHC-MASTARSSP.fits.gz

while read -r PIFU; do
  [[ -z "$PIFU" || "$PIFU" =~ ^# ]] && continue

  PLATE=${PIFU%%-*}
  IFU=${PIFU#*-}
  OUTDIR="$ROOT/$PIFU"
  mkdir -p "$OUTDIR/LOGCUBE" "$OUTDIR/MAPS"

  DRPVER="v3_1_1"
  DAPVER_DIR="3.1.0"
  PIPE="SPX-MILESHC-MASTARSSP"
  BASE="https://data.sdss.org/sas/dr17/manga/spectro/analysis/$DRPVER/$DAPVER_DIR/$PIPE/$PLATE/$IFU"
  LOGCUBE_URL="$BASE/manga-$PIFU-LOGCUBE-$PIPE.fits.gz"
  MAPS_URL="$BASE/manga-$PIFU-MAPS-$PIPE.fits.gz"

  echo "==> $PIFU: LOGCUBE を取得中"
  curl -fL --retry 3 "$LOGCUBE_URL" -o "$OUTDIR/LOGCUBE/manga-$PIFU-LOGCUBE.fits.gz" || echo "警告: $PIFU の LOGCUBE が見つかりません"

  echo "==> $PIFU: MAPS を取得中"
  curl -fL --retry 3 "$MAPS_URL" -o "$OUTDIR/MAPS/manga-$PIFU-MAPS.fits.gz" || echo "警告: $PIFU の MAPS が見つかりません"
done < "$PLATEIFU_FILE"

echo "完了: $ROOT/<plateifu>/{LOGCUBE,MAPS}/ に保存しました"
