#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch_halogas_ngc3198.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# HALOGAS DR1 (Zenodo) から NGC3198 の moment-1 (HR) を取得し、標準配置に設置
# 参照レコード: https://zenodo.org/records/2552349 （公開DR1）

OUTDIR="data/halogas/NGC3198"
VELDIR="data/vel/NGC3198"
mkdir -p "$OUTDIR" "$VELDIR"

URL_HR=${URL_HR:-"https://zenodo.org/records/2552349/files/NGC3198-HR_mom1m.fits?download=1"}

echo "HALOGAS NGC3198 HR mom1 を取得します..."
curl -fL --retry 3 "$URL_HR" -o "$OUTDIR/NGC3198-HR_mom1m.fits"
echo "保存: $OUTDIR/NGC3198-HR_mom1m.fits"

# 標準速度場パスへコピー（ベンチ/オーバーレイが自動で参照）
cp "$OUTDIR/NGC3198-HR_mom1m.fits" "$VELDIR/velocity.fits"
echo "速度場: $VELDIR/velocity.fits に配置しました"

exit 0
