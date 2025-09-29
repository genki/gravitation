#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch_halogas_ngc2403.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# HALOGAS DR1/Zenodo HR cube から NGC2403 の moment-1 を作成し標準配置へ

OUTDIR="data/halogas/NGC2403"
VELDIR="data/vel/NGC2403"
mkdir -p "$OUTDIR" "$VELDIR"

URL_CUBE=${URL_CUBE:-"https://zenodo.org/record/3715549/files/NGC2403-HR-cube.fits?download=1"}

echo "HALOGAS NGC2403 HR cube を取得します..."
curl -fL --retry 3 "$URL_CUBE" -o "$OUTDIR/NGC2403-HR-cube.fits"
echo "保存: $OUTDIR/NGC2403-HR-cube.fits"

echo "moment-1 を生成します..."
PYTHONPATH=. ./.venv/bin/python scripts/benchmarks/make_mom1_from_cube.py \
  --cube "$OUTDIR/NGC2403-HR-cube.fits" --out "$VELDIR/velocity.fits" --snr-thr 3.0
echo "速度場: $VELDIR/velocity.fits に配置しました"

exit 0
