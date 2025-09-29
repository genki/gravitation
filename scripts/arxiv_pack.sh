#!/usr/bin/env bash
if [[ ${BASH_SOURCE[0]} != "$0" ]]; then
  echo "Do not source; run ./scripts/arxiv_pack.sh" >&2
  return 1 2>/dev/null || exit 1
fi
set -euo pipefail

# arXiv 提出用パッケージを作成
# paper/ 内でビルドし、.bbl を同梱して dist/arxiv.zip を生成します。

ROOT=$(cd -- "$(dirname -- "$0")/.."; pwd)
cd "$ROOT/paper"

echo "PDF をビルド中..."
make pdf

echo "arXiv パッケージを作成中..."
make arxiv

echo "完了: paper/dist/arxiv.zip"
