#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/fetch_halpha_irsa.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# IRSA/SINGS の Hα HA_SUB を取得して標準配置へ。IRSAの安定URLが必要です。
# 使い方:
#   GAL=NGC3198 URL=https://.../HA_SUB.fits scripts/fetch_halpha_irsa.sh
# または手動で HA_SUB を取得して --in で ingest_halpha.py に渡してください。

GAL=${GAL:-NGC3198}
URL=${URL:-}
if [ -z "$URL" ]; then
  echo "ERROR: URL が未指定です。IRSAのHA_SUB FITSの直リンクを URL= で与えてください。" >&2
  echo "代替: make ha-$(echo "$GAL" | tr '[:upper:]' '[:lower:]') IN=/path/to/HA_SUB.fits" >&2
  exit 2
fi

OUTDIR="data/halpha/$GAL"
mkdir -p "$OUTDIR"

echo "IRSA Hα (HA_SUB) を取得: $URL"
curl -fL --retry 3 "$URL" -o "$OUTDIR/HA_SUB.fits"
echo "保存: $OUTDIR/HA_SUB.fits"

echo "ingest_halpha.py を実行して面輝度/EMへ変換..."
PYTHONPATH=. ./.venv/bin/python scripts/halpha/ingest_halpha.py --in "$OUTDIR/HA_SUB.fits" --name "$GAL"
echo "完了: data/halpha/$GAL/Halpha_SB.fits, EM_pc_cm6.fits"
exit 0
