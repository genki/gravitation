#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch_things.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# THINGS の HI 21cm データ（メタデータまたはサンプル）を取得
# フルデータセットは大容量のため、公開サンプルがあれば最小限のみ取得します。

OUTDIR=data/things
mkdir -p "$OUTDIR"

echo "注意: THINGS の高解像度データは大容量で、手動取得が必要な場合があります。"
echo "必要に応じて $OUTDIR/<galaxy>/*.fits に配置してください。"

# 公開ミラーがある場合は、以下に具体的なサンプル URL を追加してください。
# 例（プレースホルダ）:
# curl -fL --retry 3 "https://example.org/things/NGC3198/NGC3198_HI_mom0.fits" \
#   -o "$OUTDIR/NGC3198/NGC3198_HI_mom0.fits"

exit 0
